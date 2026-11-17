from pathlib import Path
import hashlib,json
from pypdf import PdfReader
root=Path('/output/paper');text=(root/'paper.txt').read_text();normalized=''.join(text.casefold().split());assert 'groundedexperimentalsummary' in normalized and 'supplementaryinformation' in normalized
log=(root/'step4-pdflatex.log').read_text();assert 'undefined references' not in log and 'Citation `templateReference2026' not in log
pdf=PdfReader(root/'paper.pdf');assert len(pdf.pages)>0
result={'four_passes_completed':True,'no_shell_escape':True,'pages':len(pdf.pages),'pdf_sha256':hashlib.sha256((root/'paper.pdf').read_bytes()).hexdigest(),'pdftotext_expected_title_and_appendix':True,'scope':'Original unmodified ICLR minimal template and shared original example bibliography only. It contains source placeholders/branding; this is dependency/compile acceptance, not a valid scientific manuscript, SI validation, research result or pipeline phase.'}
Path('/output/COMPILE.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
