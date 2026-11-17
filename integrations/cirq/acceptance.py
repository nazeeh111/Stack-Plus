"""Small Cirq CPU contracts, independent numerical oracles and wrong-result controls."""
from pathlib import Path
import json
import time
import cirq
import networkx as nx
import numpy as np


def rejected(operation):
    try:
        operation()
    except (AssertionError, ValueError):
        return True
    raise AssertionError('Known-wrong result was accepted')


def close(actual, expected, atol=1e-10):
    np.testing.assert_allclose(actual, expected, atol=atol, rtol=0)


def main():
    started = time.monotonic()
    assert cirq.__version__ == '1.7.0'
    checks = {}
    q0, q1, q2 = order = list(cirq.LineQubit.range(3))
    sim = cirq.Simulator(dtype=np.complex128, seed=731)
    density = cirq.DensityMatrixSimulator(dtype=np.complex128, seed=732)

    asymmetric = cirq.Circuit(cirq.X(q0), cirq.I(q1))
    state = sim.simulate(asymmetric, qubit_order=[q0, q1]).final_state_vector
    close(state, [0, 0, 1, 0])
    rejected(lambda: close(state, [0, 1, 0, 0]))
    checks['explicit_asymmetric_qubit_order'] = {'passed': True, 'reversed_order_rejected': True}

    bell = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1))
    sampled = sim.run(bell + cirq.Circuit(cirq.measure(q0, q1, key='joint')), repetitions=1024)
    bits = sampled.measurements['joint']
    assert bits.shape == (1024, 2) and np.all(bits[:, 0] == bits[:, 1])
    assert 0.4 < float(bits[:, 0].mean()) < 0.6
    # Independent marginals predict mismatches; the real joint samples do not.
    rejected(lambda: close(float(np.mean(bits[:, 0] != bits[:, 1])), 0.5))
    checks['bell_joint_samples'] = {'passed': True, 'shots': 1024, 'counts': dict(sampled.histogram(key='joint')),
                                   'independent_marginals_rejected': True}

    graph = nx.path_graph(order)
    target = cirq.CZTargetGateset()

    class LineCZDevice(cirq.Device):
        """An explicit local three-qubit model, never a Google processor claim."""
        def validate_operation(self, op):
            if not set(op.qubits) <= set(order) or not target.validate(op):
                raise ValueError('Operation outside local device/gateset')
            if len(op.qubits) == 2 and not graph.has_edge(*op.qubits):
                raise ValueError('Nonadjacent physical edge')

    logical = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q2), cirq.T(q1))
    routed, initial_map, final_map = cirq.RouteCQC(graph).route_circuit(logical)
    cirq.testing.assert_circuits_have_same_unitary_given_final_permutation(
        routed, logical.transform_qubits(initial_map), final_map)
    compiled = cirq.optimize_for_target_gateset(routed, gateset=target)
    cirq.testing.assert_allclose_up_to_global_phase(cirq.unitary(routed), cirq.unitary(compiled), atol=1e-7)
    device = LineCZDevice()
    device.validate_circuit(compiled)
    rejected(lambda: device.validate_circuit(cirq.Circuit(cirq.CZ(q0, q2))))
    rejected(lambda: device.validate_circuit(cirq.Circuit(cirq.CNOT(q0, q1))))
    checks['routing_compilation_device'] = {'passed': True, 'device': 'authored local LineCZDevice, three-qubit path',
        'initial_map': {str(k): str(v) for k, v in initial_map.items()},
        'final_swap_map': {str(k): str(v) for k, v in final_map.items()},
        'invalid_edge_and_non_native_gate_rejected': True}

    gamma = 0.23
    plus = np.array([1, 1], dtype=complex) / np.sqrt(2)
    rho0 = np.outer(plus, plus.conj())
    k0 = np.diag([1, np.sqrt(1-gamma)])
    k1 = np.array([[0, np.sqrt(gamma)], [0, 0]])
    expected = k0 @ rho0 @ k0.conj().T + k1 @ rho0 @ k1.conj().T
    rho = density.simulate(cirq.Circuit(cirq.amplitude_damp(gamma)(q0)), initial_state=plus,
                           qubit_order=[q0]).final_density_matrix
    close(rho, expected)
    close(np.trace(rho), 1)
    close(rho, rho.conj().T)
    assert np.linalg.eigvalsh(rho).min() >= -1e-10
    rejected(lambda: close(rho, rho0))
    t1, t2, duration = 50e-6, 30e-6, 12e-6
    ga = -np.expm1(-duration/t1)
    gp = -np.expm1(-2*duration*(1/t2 - 1/(2*t1)))
    thermal = cirq.Circuit(cirq.amplitude_damp(ga)(q0), cirq.phase_damp(gp)(q0))
    thermal_rho = density.simulate(thermal, initial_state=plus, qubit_order=[q0]).final_density_matrix
    close(thermal_rho[0, 1], 0.5*np.exp(-duration/t2))
    wrong = cirq.Circuit(cirq.amplitude_damp(ga)(q0), cirq.phase_damp(-np.expm1(-duration/t2))(q0))
    wrong_rho = density.simulate(wrong, initial_state=plus, qubit_order=[q0]).final_density_matrix
    rejected(lambda: close(wrong_rho[0, 1], 0.5*np.exp(-duration/t2)))
    checks['noise_kraus_and_thermal'] = {'passed': True, 'amplitude_gamma': gamma,
        'T1_seconds': t1, 'T2_seconds': t2, 'duration_seconds': duration,
        'missing_noise_and_double_counted_T2_rejected': True}

    class RecordingSimulator(cirq.Simulator):
        def __init__(self):
            super().__init__(seed=733)
            self.programs = []
        def run_sweep(self, program, params=None, repetitions=1):
            self.programs.append(program.copy())
            return super().run_sweep(program, params=params, repetitions=repetitions)

    rb_sim = RecordingSimulator()
    rb = cirq.experiments.single_qubit_rb(rb_sim, q0,
        parameters=cirq.experiments.RBParameters(num_clifford_range=[2, 4, 8], num_circuits=3, repetitions=64),
        rng_or_seed=734)
    close([prob for _, prob in rb.data], [1, 1, 1])
    assert len(rb_sim.programs) == 9
    caught = 0
    for program in rb_sim.programs:
        preparation = cirq.drop_terminal_measurements(program)
        cirq.testing.assert_allclose_up_to_global_phase(cirq.unitary(preparation), np.eye(2), atol=1e-7)
        # drop_terminal_measurements inserts identities; remove the actual final
        # inverse from the original generated operation stream instead.
        ops = [op for op in program.all_operations() if not cirq.is_measurement(op)]
        if len(ops) > 1:
            try:
                cirq.testing.assert_allclose_up_to_global_phase(cirq.unitary(cirq.Circuit(ops[:-1])), np.eye(2), atol=1e-7)
            except AssertionError:
                caught += 1
    assert caught > 0, 'RB inverse removal control did not exercise inversion'
    checks['real_clifford_RB'] = {'passed': True, 'data': rb.data, 'circuits': len(rb_sim.programs),
        'shots_per_circuit': 64, 'removed_inverse_piece_rejected': caught,
        'limit': 'Ideal inversion/survival smoke check; no error-rate fit from all-one data'}

    xeb_circuit = cirq.Circuit(cirq.ry(0.4)(q0), cirq.rx(0.8)(q1), cirq.CZ(q0, q1))
    xeb_samples = sim.run(xeb_circuit + cirq.Circuit(cirq.measure(q0, q1, key='xeb')), repetitions=512)
    ints = [int(row[0])*2 + int(row[1]) for row in xeb_samples.measurements['xeb']]
    probs = np.abs(sim.simulate(xeb_circuit, qubit_order=[q0, q1]).final_state_vector)**2
    oracle = float(4*np.mean(probs[ints])-1)
    xeb = cirq.experiments.xeb_fidelity(xeb_circuit, ints, qubit_order=[q0, q1])
    close(xeb, oracle, atol=1e-6)
    rejected(lambda: close(xeb, float(np.mean(np.log(probs[ints]))), atol=1e-6))
    checks['linear_XEB'] = {'passed': True, 'shots': 512, 'value': float(xeb),
        'logarithmic_substitution_rejected': True, 'limit': 'Small API estimator check, not a fidelity experiment'}

    restored = cirq.read_json(json_text=cirq.to_json({'circuit': bell, 'result': sampled,
                                                   'qubit_order': [q0, q1], 'version': cirq.__version__}))
    assert restored['circuit'] == bell and restored['qubit_order'] == [q0, q1]
    np.testing.assert_array_equal(restored['result'].measurements['joint'], bits)
    checks['lossless_circuit_result_order_archive'] = {'passed': True}
    result = {'passed': True, 'cirq_version': cirq.__version__, 'elapsed_seconds': time.monotonic()-started,
              'checks': checks, 'limits': ['CPU synthetic fixtures only', 'No Google/vendor device, QVM, cloud, QPU or credentials',
                  'No QEC, quantum advantage, threshold, calibration or research-validity claim']}
    Path('RESULT.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
