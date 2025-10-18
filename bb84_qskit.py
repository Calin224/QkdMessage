from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
import numpy as np
import random
from typing import List
from qiskit_aer import AerSimulator

class Sender:
    def __init__(self, key_length=5):
        self.key_length = key_length
        self.bits = []
        self.bases = []
    
    def generate_bits(self):
        self.bits = [random.randint(0, 1) for _ in range(self.key_length)]
        return self.bits
    
    def choose_bases(self):
        self.bases = [random.choice([0, 1]) for _ in range(self.key_length)]
        return self.bases
    
    def encode_qubits(self, bits=None, bases=None):
        if bits is None:
            bits = self.bits
        if bases is None:
            bases = self.bases
            
        circuits = []
        for bit, basis in zip(bits, bases):
            qc = QuantumCircuit(1, 1)
            if basis == 0: 
                if bit == 1:
                    qc.x(0)
            else: 
                if bit == 0:
                    qc.h(0)
                else:
                    qc.x(0)
                    qc.h(0)
            circuits.append(qc)
        return circuits

class Receiver:
    def __init__(self, key_length=5):
        self.key_length = key_length
        self.bases = []
        self.measurement_results = []
    
    def choose_bases(self):
        self.bases = [random.choice([0, 1]) for _ in range(self.key_length)]
        return self.bases
    
    def measure_qubits(self, circuits, bases=None):
        if bases is None:
            bases = self.bases
            
        measured_circuits = []
        for qc, basis in zip(circuits, bases):
            measured_qc = qc.copy()
            if basis == 1: 
                measured_qc.h(0)
            measured_qc.measure(0, 0)
            measured_circuits.append(measured_qc)
        return measured_circuits
    
    def extract_key(self, measurement_results, alice_bases, bob_bases):
        return [bit for i, bit in enumerate(measurement_results) 
                if alice_bases[i] == bob_bases[i]]

class BB84:
    def __init__(self, key_length=5):
        self.key_length = key_length
        self.sender = Sender(key_length)
        self.receiver = Receiver(key_length)
        self.shared_key = []
    
    def build_circuits(self, alice_bits, alice_bases, bob_bases):
        alice_circuits = self.sender.encode_qubits(alice_bits, alice_bases)
        bob_circuits = self.receiver.measure_qubits(alice_circuits, bob_bases)
        
        num_of_qubits = len(alice_bits)
        qc = QuantumCircuit(num_of_qubits, num_of_qubits)
        
        for i, alice_qc in enumerate(alice_circuits):
            for instruction in alice_qc.data:
                if instruction.operation.name == 'x':
                    qc.x(i)
                elif instruction.operation.name == 'h':
                    qc.h(i)
        
        qc.barrier()
        
        for i, bob_qc in enumerate(bob_circuits):
            for instruction in bob_qc.data:
                if instruction.operation.name == 'h':
                    qc.h(i)
                elif instruction.operation.name == 'measure':
                    qc.measure(i, i)
        
        return qc
    
    def run(self):
        alice_bits = self.sender.generate_bits()
        alice_bases = self.sender.choose_bases()
        
        bob_bases = self.receiver.choose_bases()
        
        print(f"Alice bits: {alice_bits}")
        print(f"Alice bases: {alice_bases}")
        print(f"Bob bases: {bob_bases}")
        
        full_circuit = self.build_circuits(alice_bits, alice_bases, bob_bases)
        
        backend = AerSimulator()
        transpiled_result = transpile(full_circuit, backend)
        job = backend.run(transpiled_result, shots=1)
        result = job.result()
        counts = result.get_counts()
        
        measurement_result = list(counts.keys())[0] 
        bob_bits_raw = [int(bit) for bit in measurement_result.replace(' ', '')]
        bob_bits = bob_bits_raw[:self.key_length][::-1]
        
        print(f"Bob measurement result: {bob_bits}")
        
        self.shared_key = self.receiver.extract_key(bob_bits, alice_bases, bob_bases)
        
        print(f"Final shared key: {self.shared_key}")
        print(f"Key length: {len(self.shared_key)}")
        
        return self.shared_key

bb84 = BB84(key_length=5)
bb84.run()