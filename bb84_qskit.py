from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
import numpy as np
import random
from typing import List
from qiskit_aer import AerSimulator

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
            
        qc.draw()
        return qc
    
    def remove_garbage(self,a_bases,b_bases,bits):
        result = []
        for i, bit in enumerate(bits):
            if a_bases[i] == b_bases[i]:
                result.append(bit)
        return result

    def run(self):
        self.generate_alice_bits()
        self.choose_alice_bases()

        message = self.encode_messag(self.alice_bits,self.alice_bases)
        
        self.choose_bob_bases()
        bob_circuits =  self.measure_message(message,self.bob_bases)
        full_circuit = self.build_circuits(self.alice_bits,self.alice_bases,self.bob_bases)

        backend = AerSimulator()
        transpiled_result = transpile(full_circuit, backend)
        job = backend.run(transpiled_result)
        result = job.result()
        counts = result.get_counts()

        print(f"Key: {counts}")

bb84 = BB84(key_length=20)
bb84.run()

    



    