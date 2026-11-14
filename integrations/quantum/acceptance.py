"""Small local CPU quantum oracles; no provider, device, browser or model calls."""
import errno
import importlib.metadata as metadata
import json
import math
import platform
import socket
import sys
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.primitives import StatevectorEstimator, StatevectorSampler
from qiskit.quantum_info import SparsePauliOp, Statevector
import qutip as qt
import pennylane as qml
from pennylane import numpy as pnp


def close(actual, expected, tolerance=1e-8):
    return bool(np.allclose(actual, expected, rtol=tolerance, atol=tolerance))


def must_reject(check):
    try:
        check()
    except AssertionError:
        return True
    raise AssertionError('Intentionally wrong control was accepted')


def require_close(actual, expected, tolerance=1e-8):
    assert close(actual, expected, tolerance), (actual, expected)


def physical(states):
    matrices=[s.proj().full() if s.isket else s.full() for s in states]
    result={'trace_error':max(float(abs(np.trace(r)-1)) for r in matrices),
            'hermitian_error':max(float(np.linalg.norm(r-r.conj().T)) for r in matrices),
            'minimum_eigenvalue':min(float(np.linalg.eigvalsh(r).min()) for r in matrices)}
    assert result['trace_error']<1e-8 and result['hermitian_error']<1e-8
    assert result['minimum_eigenvalue']>=-1e-8
    return result

report={'python':sys.version,'machine':platform.machine(),'versions':{},'provider_calls':0,'hardware_jobs':0}
for package,expected in [('qiskit','2.5.2'),('qutip','5.3.1'),('pennylane','0.45.1')]:
    actual=metadata.version(package);assert actual==expected
    report['versions'][package]=actual
for package in ['numpy','scipy','pennylane-lightning']:
    report['versions'][package]=metadata.version(package)
for forbidden in ['qiskit-ibm-runtime','torch','jax','pennylane-catalyst']:
    try:metadata.version(forbidden)
    except metadata.PackageNotFoundError:continue
    raise AssertionError('Unneeded provider/GPU/ML extra installed: '+forbidden)
try:
    socket.create_connection(('127.0.0.1',9),timeout=1)
except OSError as error:
    report['network_os_denied']=error.errno in (errno.EPERM,errno.EACCES)
else:report['network_os_denied']=False
assert report['network_os_denied']

# Independent two-qubit basis oracle plus sampled and exact V2 primitives.
bell=QuantumCircuit(2);bell.h(0);bell.cx(0,1)
state=Statevector.from_instruction(bell)
expected_state=np.array([1/math.sqrt(2),0,0,1/math.sqrt(2)],dtype=complex)
require_close(state.data,expected_state,1e-12)
observables=[SparsePauliOp.from_list([(name,1.0)]) for name in ['XX','YY','ZZ']]
estimate=StatevectorEstimator(seed=19).run([(bell,o) for o in observables]).result()
correlators=[float(x.data.evs) for x in estimate]
require_close(correlators,[1,-1,1],1e-12)
measured=bell.copy();measured.measure_all()
counts=StatevectorSampler(seed=19).run([measured],shots=2048).result()[0].data.meas.get_counts()
assert set(counts)=={'00','11'} and sum(counts.values())==2048
assert all(0.4<n/2048<0.6 for n in counts.values())
asymmetric=QuantumCircuit(2);asymmetric.x(0);asymmetric.measure_all()
asymmetric_counts=StatevectorSampler(seed=19).run([asymmetric],shots=64).result()[0].data.meas.get_counts()
assert asymmetric_counts=={'01':64}
compiled=transpile(bell,basis_gates=['rz','sx','x','cx'],optimization_level=1,seed_transpiler=19)
assert state.equiv(Statevector.from_instruction(compiled))
report['qiskit']={'bell_correlators':dict(zip(['XX','YY','ZZ'],correlators)),
                 'bell_counts':counts,'asymmetric_qubit0_counts':asymmetric_counts,
                 'transpile_state_equivalent':True,
                 'wrong_ZZ_control_rejected':must_reject(lambda:require_close(correlators[2],0.0)),
                 'wrong_bit_order_control_rejected':must_reject(lambda:require_close([asymmetric_counts.get('10',0)],[64]))}

# QuTiP exact unitary solution and a Markovian amplitude damping solution.
omega=1.7;t=np.linspace(0,2*np.pi/omega,101);initial=qt.basis(2,0)
unitary=qt.sesolve(0.5*omega*qt.sigmax(),initial,t,e_ops=[initial.proj()],
 options={'atol':1e-11,'rtol':1e-10,'store_states':True,'normalize_output':False,'progress_bar':''})
unitary_error=float(np.max(np.abs(np.asarray(unitary.expect[0])-np.cos(omega*t/2)**2)))
assert unitary_error<1e-7
unitary_metrics=physical(unitary.states)
gamma=0.37;times=np.linspace(0,7.3,75);hamiltonian=0.5*qt.sigmaz();collapse=[math.sqrt(gamma)*qt.sigmam()]
reference=np.exp(-gamma*times)
errors={};solutions={}
for label,atol,rtol in [('coarse',1e-5,1e-4),('fine',1e-11,1e-10)]:
    result=qt.mesolve(hamiltonian,initial,times,c_ops=collapse,e_ops={'population':initial.proj()},
      options={'atol':atol,'rtol':rtol,'store_states':True,'normalize_output':False,'progress_bar':''})
    solutions[label]=result
    errors[label]=float(np.max(np.abs(np.asarray(result.e_data['population'])-reference)))
assert errors['fine']<1e-7 and errors['fine']<=errors['coarse']+1e-10
open_metrics=physical(solutions['fine'].states)
wrong_rate_rejected=must_reject(lambda:require_close(solutions['fine'].e_data['population'],np.exp(-gamma**2*times),1e-6))
report['qutip']={'unitary_max_abs_error':unitary_error,'unitary_state_invariants':unitary_metrics,
 'open_max_abs_errors':errors,'open_state_invariants':open_metrics,
 'last_population':float(solutions['fine'].e_data['population'][-1]),'exact_last_population':float(reference[-1]),
 'wrong_collapse_rate_control_rejected':wrong_rate_rejected,
 'negative_density_control_rejected':must_reject(lambda:physical([qt.Qobj([[1.1,0],[0,-0.1]])])),
 'invalid_trace_control_rejected':must_reject(lambda:physical([qt.Qobj([[0.8,0],[0,0.8]])])),
 'solver_stats':{k:v for k,v in solutions['fine'].stats.items() if isinstance(v,(str,float,int,bool))}}

# PennyLane default CPU simulator, independent cos/-sin and finite differences.
dev=qml.device('default.qubit',wires=1)
@qml.qnode(dev,interface='autograd',diff_method='backprop')
def energy(theta):
    qml.RY(theta,wires=0)
    return qml.expval(qml.Z(0))
rows=[]
for angle in [0.317,-0.73,1.21]:
    theta=pnp.array(angle,requires_grad=True)
    value=float(energy(theta));gradient=float(qml.grad(energy)(theta));h=1e-6
    finite=float((energy(theta+h)-energy(theta-h))/(2*h))
    require_close(value,math.cos(angle),1e-10)
    require_close(gradient,-math.sin(angle),1e-10)
    require_close(gradient,finite,1e-8)
    rows.append({'theta':angle,'expectation':value,'gradient':gradient,'exact_gradient':-math.sin(angle),'finite_difference':finite})
wrong_gradient=must_reject(lambda:require_close(rows[0]['gradient'],math.sin(rows[0]['theta']),1e-8))
theta=pnp.array(0.3,requires_grad=True);optimizer=qml.GradientDescentOptimizer(stepsize=0.2)
for _ in range(80):theta=optimizer.step(energy,theta)
final_value=float(energy(theta));assert final_value < -0.999
report['pennylane']={'device':'default.qubit','analytic_and_finite_difference':rows,'wrong_gradient_sign_rejected':wrong_gradient,'optimization_steps':80,'final_expectation_recomputed':final_value}
report['passed']=True
Path('ACCEPTANCE.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
