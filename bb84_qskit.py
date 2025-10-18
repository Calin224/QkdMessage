from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
import numpy as np
import random
from typing import List
from qiskit_aer import AerSimulator

class Sender:
    """Clasa pentru Alice (Sender) în protocolul BB84"""
    def __init__(self, key_length=5):
        self.key_length = key_length
        self.bits = []
        self.bases = []
    
    def generate_bits(self):
        """Generează biti aleatorii"""
        self.bits = [random.randint(0, 1) for _ in range(self.key_length)]
        return self.bits
    
    def choose_bases(self):
        """Alege baze aleatorii pentru măsurare"""
        self.bases = [random.choice([0, 1]) for _ in range(self.key_length)]
        return self.bases
    
    def encode_qubits(self, bits=None, bases=None):
        """Encodează bitii în qubiti folosind bazele specificate"""
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
    """Clasa pentru Bob (Receiver) în protocolul BB84"""
    def __init__(self, key_length=5):
        self.key_length = key_length
        self.bases = []
        self.measurement_results = []
    
    def choose_bases(self):
        """Alege baze aleatorii pentru măsurare"""
        self.bases = [random.choice([0, 1]) for _ in range(self.key_length)]
        return self.bases
    
    def measure_qubits(self, circuits, bases=None):
        """Măsoară qubitii în bazele specificate"""
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
        """Extrage cheia comună din măsurătorile cu baze identice"""
        return [bit for i, bit in enumerate(measurement_results) 
                if alice_bases[i] == bob_bases[i]]

class Eavesdropper:
    """Clasa pentru Eve (Eavesdropper) în protocolul BB84"""
    def __init__(self, key_length=5):
        self.key_length = key_length
        self.bases = []
        self.intercepted_bits = []
        self.qber = 0.0
    
    def choose_bases(self):
        """Eve alege baze aleatorii pentru interceptare"""
        self.bases = [random.choice([0, 1]) for _ in range(self.key_length)]
        return self.bases
    
    def intercept_and_measure(self, circuits, bases=None):
        """Eve interceptează și măsoară qubitii"""
        if bases is None:
            bases = self.bases
            
        intercepted_circuits = []
        for qc, basis in zip(circuits, bases):
            intercepted_qc = qc.copy()
            if basis == 1:
                intercepted_qc.h(0)
            intercepted_qc.measure(0, 0)
            intercepted_circuits.append(intercepted_qc)
        return intercepted_circuits
    
    def resend_qubits(self, intercepted_bits, alice_bases):
        """Eve re-transmite qubitii către Bob (cu erori datorate măsurătorii)"""
        resent_circuits = []
        for bit, alice_basis in zip(intercepted_bits, alice_bases):
            qc = QuantumCircuit(1, 1)
            if alice_basis == 0: 
                if bit == 1:
                    qc.x(0)
            else:
                if bit == 0:
                    qc.h(0)
                else:
                    qc.x(0)
                    qc.h(0)
            resent_circuits.append(qc)
        return resent_circuits
    
    def get_intercepted_key(self, alice_bases, bob_bases):
        eve_key = []
        for i in range(len(self.bases)):
            if alice_bases[i] == self.bases[i]:
                eve_key.append(self.intercepted_bits[i])
        return eve_key
    
    def calculate_qber(self, alice_bits, alice_bases, bob_bits, bob_bases):
        """Calculează QBER (Quantum Bit Error Rate)"""
        errors = 0
        total_measurements = 0
        
        for i in range(len(alice_bits)):
            if alice_bases[i] == bob_bases[i]:
                total_measurements += 1
                if alice_bits[i] != bob_bits[i]:
                    errors += 1
        
        if total_measurements > 0:
            self.qber = errors / total_measurements
        else:
            self.qber = 0.0
            
        return self.qber

class BB84:
    """Clasa principală pentru protocolul BB84"""
    def __init__(self, key_length=5, include_eve=False):
        self.key_length = key_length
        self.sender = Sender(key_length)
        self.receiver = Receiver(key_length)
        self.eavesdropper = Eavesdropper(key_length) if include_eve else None
        self.shared_key = []
        self.include_eve = include_eve
    
    def build_circuits(self, alice_bits, alice_bases, bob_bases):
        """Construiește circuitul complet folosind funcțiile generice"""
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
    
    def detect_eve(self, alice_bits, alice_bases, bob_bases, bob_bits):
        """Detectează prezența lui Eve prin calcularea QBER"""
        qber = self.eavesdropper.calculate_qber(alice_bits, alice_bases, bob_bits, bob_bases)
        
        print(f"QBER (Quantum Bit Error Rate): {qber:.3f}")
        
        eve_detected = qber > 0.11
        
        if eve_detected:
            print("🚨 EVE DETECTED! QBER exceeds threshold (11%)")
        else:
            print("✅ No Eve detected. QBER within normal range.")
            
        return eve_detected
    
    def run_with_eve(self):
        """Rulează protocolul BB84 cu Eve prezentă"""
        alice_bits = self.sender.generate_bits()
        alice_bases = self.sender.choose_bases()
        
        bob_bases = self.receiver.choose_bases()
        
        eve_bases = self.eavesdropper.choose_bases()
        
        print(f"Alice bits: {alice_bits}")
        print(f"Alice bases: {alice_bases}")
        print(f"Bob bases: {bob_bases}")
        print(f"Eve bases: {eve_bases}")
        
        alice_circuits = self.sender.encode_qubits(alice_bits, alice_bases)
        
        eve_circuits = self.eavesdropper.intercept_and_measure(alice_circuits, eve_bases)
        
        backend = AerSimulator()
        eve_bits = []
        for i, qc in enumerate(eve_circuits):
            transpiled = transpile(qc, backend)
            job = backend.run(transpiled, shots=1)
            result = job.result()
            counts = result.get_counts()
            measurement = list(counts.keys())[0]
            eve_bits.append(int(measurement.replace(' ', '')))
        
        self.eavesdropper.intercepted_bits = eve_bits
        print(f"Eve intercepted bits: {eve_bits}")
        
        resent_circuits = self.eavesdropper.resend_qubits(eve_bits, alice_bases)
        
        bob_circuits = self.receiver.measure_qubits(resent_circuits, bob_bases)
        
        bob_bits = []
        for i, qc in enumerate(bob_circuits):
            transpiled = transpile(qc, backend)
            job = backend.run(transpiled, shots=1)
            result = job.result()
            counts = result.get_counts()
            measurement = list(counts.keys())[0]
            bob_bits.append(int(measurement.replace(' ', '')))
        
        print(f"Bob measurement result: {bob_bits}")
        
        eve_detected = self.detect_eve(alice_bits, alice_bases, bob_bases, bob_bits)
        
        if eve_detected:
            print("🚨 EVE DETECTED! Communication compromised.")
            return None
        else:
            self.shared_key = self.receiver.extract_key(bob_bits, alice_bases, bob_bases)
            print(f"Final shared key: {self.shared_key}")
            print(f"Key length: {len(self.shared_key)}")
            
            eve_key = self.eavesdropper.get_intercepted_key(alice_bases, bob_bases)
            print(f"Eve's attempted key: {eve_key}")
            
            print(f"\n=== QBER Statistics ===")
            print(f"QBER: {self.eavesdropper.qber:.3f} ({self.eavesdropper.qber*100:.1f}%)")
            print(f"Eve detection threshold: 11%")
            print(f"Status: {'EVE DETECTED' if self.eavesdropper.qber > 0.11 else 'SECURE'}")
            
            return self.shared_key
    
    def run(self):
        """Rulează protocolul BB84 complet"""
        if self.include_eve:
            return self.run_with_eve()
        
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

print("=== BB84 fără Eve ===")
bb84_normal = BB84(key_length=5, include_eve=False)
bb84_normal.run()

print("\n=== BB84 cu Eve (Eavesdropper) ===")
bb84_with_eve = BB84(key_length=5, include_eve=True)
bb84_with_eve.run()

    



    