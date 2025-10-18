from qiskit import QuantumCircuit, transpile
import numpy as np
import random
from typing import List

class BB84:
    def __init__(self, key_length=5):
        self.key_length = key_length

        self.polarization_map = {
            ('+', 0): '→',
            ('+', 1): '↑',
            ('x', 0): '↗',
            ('x', 1): '↖',
        }

        self.alice_bits = []
        self.alice_bases = []
        # self.alice_polarizations = []

        self.bob_bases = []
        # self.bob_measurements = []

        # self.alice_key = []
        # self.bob_key = []

        self.key = []

    def generate_alice_bits(self):
        self.alice_bits = [random.randint(0, 1) for _ in range(self.key_length)]

    def choose_alice_bases(self):
        self.alice_bases = [random.choice(['+', 'x']) for _ in range(self.key_length)]

    # def alice_polarization(self):
    #     self.alice_polarizations = []

    #     for bit, basis in zip(self.alice_bits, self.alice_bases):
    #         polarization = self.polarization_map[(basis, bit)]
    #         self.alice_polarizations.append(polarization)

    def choose_bob_bases(self):
        self.bob_bases = [random.choice(['+', 'x']) for _ in range(self.key_length)]

    # def transmit_qubits(self) -> List[int]:
    #     transmited_qubits = []

    #     for i in range(len(self.alice_bits)):
    #         bit = self.alice_bits[i]

    #         transmited_qubits.append(bit)

    #     return transmited_qubits

    # def measure_qubits(self, transmitted_qubits: List[int]):
    #     self.bob_measurements = []

    #     for i in range(len(transmitted_qubits)):
    #         bit = transmitted_qubits[i]
    #         alice_basis = self.alice_bases[i]
    #         bob_basis = self.bob_bases[i]

    #         if bob_basis != alice_basis:
    #             measured_bit = random.choice([0, 1])
    #         elif bob_basis == alice_basis:
    #             measured_bit = bit
        
    #         self.bob_measurements.append(measured_bit)

    def compute_bob_key(self, alice_bit, alice_basis, bob_basis):
        if alice_basis == bob_basis:
            self.key.append(alice_bit)


    # def sort_keys(self):
    #     self.matching_bases_indices = []
    #     self.alice_key = []
    #     self.bob_key = []

    #     for i in range(len(self.alice_bits)):
    #         if self.alice_bases[i] == self.bob_bases[i]:
    #             self.matching_bases_indices.append(i)
    #             self.alice_key.append(self.alice_bits[i])
    #             self.bob_key.append(self.bob_measurements[i])

    def run(self):
        self.generate_alice_bits()
        self.choose_alice_bases()

        self.choose_bob_bases()

        for i in range(len(self.alice_bits)):
            self.compute_bob_key(self.alice_bits[i], self.alice_bases[i], self.bob_bases[i])

        print(f"Key: {self.key}")

bb84 = BB84(key_length=20)
bb84.run()

    



    