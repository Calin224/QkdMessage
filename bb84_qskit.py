from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
import numpy as np
import random
from typing import List
from qiskit_aer import AerSimulator

# Eave
class BB84:
    def __init__(self, key_length=5):
        self.key_length = key_length

        self.alice_bits = []
        self.alice_bases = []

        self.bob_bases = []
        self.key = []

    def generate_alice_bits(self):
        self.alice_bits = [random.randint(0, 1) for _ in range(self.key_length)]

    def choose_alice_bases(self):
        self.alice_bases = [random.choice([0,1] ) for _ in range(self.key_length)]

    def choose_bob_bases(self): 
        self.bob_bases = [random.choice([0,1]) for _ in range(self.key_length)]

    def compute_bob_key(self, alice_bit, alice_basis, bob_basis):
        if alice_basis == bob_basis:
            self.key.append(alice_bit)


    def encode_messag(self,bits,bases):
        circuits = []
        for bit, basis in zip(bits,bases):
            qc = QuantumCircuit(1,1)
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
        
    def measure_message(self,circuits,bases):
        measured_circuits = []
        for qc,basis in zip(circuits,bases):
            measured_qc = qc.copy()
            if basis == 1: 
                measured_qc.h(0)  
            measured_qc.measure(0,0)
            measured_circuits.append(measured_qc)
        return measured_circuits
    
    def build_circuits(self,alice_bits,alice_bases,bob_bases):
        num_of_qubits = len(alice_bits)
        qc = QuantumCircuit(num_of_qubits,num_of_qubits)
        
        for i in range(num_of_qubits):
            if alice_bases[i]==0:  
                if alice_bits[i]==1:
                    qc.x(i)  
            else:  
                if alice_bits[i]==0:
                    qc.h(i)  
                else:
                    qc.x(i)
                    qc.h(i)  
        
        qc.barrier()
        
        for i in range(num_of_qubits):
            if bob_bases[i]==1:  
                qc.h(i)
        
        qc.measure_all()
        return qc
    
    def remove_garbage(self,a_bases,b_bases,bits):
        return [bit for i, bit in enumerate(bits) if a_bases[i] == b_bases[i]]
        

    def run(self):
        self.generate_alice_bits()
        self.choose_alice_bases()
        self.choose_bob_bases()
        
        print(f"Alice bits: {self.alice_bits}")
        print(f"Alice bases: {self.alice_bases}")
        print(f"Bob bases: {self.bob_bases}")
        
        full_circuit = self.build_circuits(self.alice_bits, self.alice_bases, self.bob_bases)
        
        backend = AerSimulator()
        transpiled_result = transpile(full_circuit, backend)
        job = backend.run(transpiled_result, shots=1)
        result = job.result()
        counts = result.get_counts()
        
        measurement_result = list(counts.keys())[0] 
        bob_bits_raw = [int(bit) for bit in measurement_result.replace(' ', '')]
        bob_bits = bob_bits_raw[:self.key_length][::-1]
        
        print(f"Bob measurement result: {bob_bits}")
        
        final_key = self.remove_garbage(self.alice_bases, self.bob_bases, bob_bits)
        
        print(f"Final shared key: {final_key}")
        print(f"Key length: {len(final_key)}")
        
        return final_key

bb84 = BB84(key_length=5)
bb84.run()

    



    