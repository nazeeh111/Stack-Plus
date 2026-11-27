"""Resolve reviewed local skill identities under the native OpenCode permission projection."""
import argparse
import fnmatch
import json
import os
from pathlib import Path
import subprocess


def native(arguments, project):
    command = ["opencode", *arguments]
    result = subprocess.run(command, cwd=project, capture_output=True, text=True, timeout=15)
    if result.returncode:
        # Native output may include private config or provider data.
        raise ValueError(f"OpenCode did not return metadata for {arguments[1]}.")
    return result.stdout


def api(project, operation, **parameters):
    arguments = ["api", operation, "--param", f"location[directory]={project}"]
    for key, value in parameters.items():
        arguments.extend(["--param", f"{key}={value}"])
    parsed = json.loads(native(arguments,project))
    return parsed.get("data",parsed) if isinstance(parsed,dict) else parsed


def match(pattern, value):
    # OpenCode wildcards support * and ?. Square brackets are literal.
    brackets = {"[":"[[]", "]":"[]]"}
    pattern = "".join(brackets.get(char,char) for char in pattern)
    return fnmatch.fnmatchcase(value, pattern)


def permitted(rules, action, resource, default="allow"):
    effect = default
    for rule in rules:
        if match(rule.get("action",""),action) and match(rule.get("resource",""),resource):
            effect = rule["effect"]
    return effect=="allow"


def skill_policy(layers, name):
    # Native policy layers have independent authority; a tighter layer can deny.
    return all(permitted(layer,"skill.use",name)
               and permitted(layer,"integration.use","skill:"+name)
               and permitted(layer,"tool.use","skill:"+name)
               for layer in layers)


def filesystem_entries(root):
    if not root.is_dir():
        return
    todo = [(root,0)]
    while todo:
        folder, depth = todo.pop()
        entry = folder/"SKILL.md"
        if entry.is_file():
            yield folder.name, entry
            continue
        if depth>=6:
            continue
        for child in sorted(folder.iterdir(), reverse=True):
            if child.name.startswith(".") or child.name=="node_modules":
                continue
            if child.is_symlink():
                # A native skill link targets its entry. Do not descend through arbitrary linked trees.
                linked = child / "SKILL.md"
                if child.is_dir() and accept_path(linked.resolve()):
                    yield child.name, linked
                continue
            if child.is_dir() and child.resolve() not in (folder.resolve(), *folder.resolve().parents):
                todo.append((child,depth+1))
            elif depth==0 and child.is_file() and child.suffix==".md":
                yield child.stem, child


def locations(project, home):
    for directory in [project,*project.parents]:
        if directory in (directory.parent, home):
            break
        yield directory
        if (directory/".git").exists():
            break


def roots(project, home, config, sources):
    scope = list(reversed(tuple(locations(project,home))))
    if not os.environ.get("OPENCODE_DISABLE_CLAUDE_CODE"):
        yield home/".claude/skills","user"
        yield from ((folder/".claude/skills","project") for folder in scope)
    yield home/".agents/skills","user"
    yield from ((folder/".agents/skills","project") for folder in scope)
    yield config/"skill","user"
    yield config/"skills","user"
    for folder in scope:
        yield folder/".opencode/skill","project"
        yield folder/".opencode/skills","project"
    for source in sources:
        for configured in source.get("info",{}).get("skills",[]):
            if not isinstance(configured,str) or "://" in configured:
                continue
            path = Path(configured).expanduser()
            path = project/path if not path.is_absolute() else path
            yield path,"project" if path.is_relative_to(scope[0] if scope else project) else "user"


def accept_path(path):
    blocked = {".aws",".ssh",".gnupg",".kube",".git","node_modules","credentials","secrets","keychains"}
    return path.is_file() and not any(part.casefold() in blocked for part in path.parts)


def eligibility(project, agent, session, candidates):
    lines = native(["debug","paths"],project).splitlines()
    paths = {line.split(None,1)[0]:line.split(None,1)[1] for line in lines}
    home = Path(paths["home"]).resolve(strict=True)
    config = Path(paths["config"]).resolve(strict=True)
    sources = api(project,"config.get")
    session_rules = []
    if session:
        found = api(project,"session.get",sessionID=session)
        if Path(found["location"]["directory"]).resolve()!=project:
            raise ValueError("The OpenCode session belongs to a different project location.")
        selected_agent = found.get("agent")
        if agent and selected_agent and agent!=selected_agent:
            raise ValueError("The requested agent differs from the native session selection.")
        agent = selected_agent or agent
        session_rules = found.get("permissions",[])
    if agent:
        agents = [api(project,"agent.get",agentID=agent)]
    else:
        agents = [row for row in api(project,"agent.list") if row.get("mode")=="primary" and not row.get("hidden")]
        if not agents:
            configured = {name for source in sources for name, value in source.get("info",{}).get("agents",{}).items()
                          if value.get("mode")=="primary"}
            agents = [api(project,"agent.get",agentID=name) for name in sorted({"build","plan"} | configured)]
    if not agents or any("permissions" not in item for item in agents):
        raise ValueError("OpenCode did not provide the effective selected-agent permission rules.")
    rules = [item["permissions"]+session_rules for item in agents]
    documents = [source.get("info",{}) for source in sources]
    policies = [document.get("policies",[]) for document in documents]
    # A running native location may still have a cached effective agent. Respect
    # any newer denial visible in the native configuration-source projection.
    rules.extend(document.get("permissions",[]) for document in documents)
    rules.extend(document.get("agents",{}).get(item["id"],{}).get("permissions",[])
                 for document in documents for item in agents)

    def allowed(name):
        return skill_policy(policies,name) and all(permitted(row,"skill",name) for row in rules)

    winners = {}
    for root, scope in roots(project,home,config,sources):
        for name, path in filesystem_entries(root):
            if path.is_file():
                winners[name] = (path.resolve(strict=True),scope)
    disagreements = set()
    for row in api(project,"skill.list"):
        raw = Path(row["path"])
        if raw.is_absolute() and raw.is_file():
            path = raw.resolve(strict=True)
            name = row["id"]
            if name in winners and winners[name][0] != path:
                disagreements.add(name)
            elif name not in winners:
                winners[name] = (path,"project" if raw.is_relative_to(project) else "user")
    eligible = [{"name":name,"path":str(path),"scope":scope} for name,(path,scope) in sorted(winners.items())
                if path.name=="SKILL.md" and name not in disagreements and allowed(name) and accept_path(path)]
    return {"eligible":eligible,"on_demand":sorted({name for name in candidates if name not in winners and allowed(name)})}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project",required=True,type=Path)
    parser.add_argument("--agent")
    parser.add_argument("--session")
    parser.add_argument("--candidate",action="append",default=[])
    args = parser.parse_args()
    try:
        result = eligibility(args.project.resolve(strict=True),args.agent,args.session,args.candidate)
    except (OSError,ValueError,KeyError,TypeError,subprocess.TimeoutExpired) as error:
        parser.error(str(error))
    print(json.dumps(result))


if __name__ == "__main__":
    main()
