import random
from typing import List, Tuple, Optional

#simulare mesaj care are emitator si receptor
class Message:
    def __init__(self, sender_name: str, receiver_name: str, message_type: str, data):
        self.sender_name = sender_name
        self.receiver_name = receiver_name
        self.message_type = message_type  # 'qubits' / 'bases' / 'encrypted'
        self.data = data

#simulare canal care poate fi ascultat de eve
class CommunicationChannel:
    def __init__(self):
        self.messages = []
        self.eavesdroppers = []
    
    def send_message(self, message: Message):
       # print(f"Se trimit {message.message_type} de la {message.sender_name} la {message.receiver_name}")
        self.messages.append(message)
        
        for eavesdropper in self.eavesdroppers:
            if eavesdropper.name != message.sender_name:
                eavesdropper._inbox = message
                #print(f"Asculta si {eavesdropper.name}")
    
    def register_eavesdropper(self, eavesdropper):
        self.eavesdroppers.append(eavesdropper)
        print(f"A venit si {eavesdropper.name} pe canal")

class BB84Protocol:
    
    def __init__(self, key_length: int = 100):
        self.key_length = key_length
        self.current_polarizations = []
        self.original_polarizations = []
        self.eve_detected = False
        
        self.polarization_map = {
            ('+', 0): '→',
            ('+', 1): '↑',
            ('x', 0): '↗',
            ('x', 1): '↖',
        }

        self.reverse_polarization_map = {
            '→': ('+', 0),
            '↑': ('+', 1),
            '↗': ('x', 0),
            '↖': ('x', 1),
        }
    
    def generate_random_bits(self, length: int = None) -> List[int]:
        if length is None:
            length = self.key_length
        return [random.randint(0, 1) for _ in range(length)]
    
    def generate_random_bases(self, length: int = None) -> List[str]:
        if length is None:
            length = self.key_length
        return [random.choice(['+', 'x']) for _ in range(length)]
    
    # alice polarizeaza fotonii. mereu cand se modifica fotonii, se retin in current_polarizations
    def polarize_photons(self, bits: List[int], bases: List[str]) -> List[str]:
        polarizations = []
        for bit, basis in zip(bits, bases):
            polarization = self.polarization_map[(basis, bit)]
            polarizations.append(polarization)
        self.current_polarizations = polarizations
        self.original_polarizations = polarizations.copy()
        return polarizations
    
    # bob masoara fotonii, si tot asa cand se modifica fotonii se retin in current_polarizations
    def measure_photons(self, measurement_bases: List[str]) -> List[str]:
        resulting_polarizations = []
        
        for i, (polarization, basis) in enumerate(zip(self.current_polarizations, measurement_bases)):
            original_basis, original_bit = self.reverse_polarization_map[polarization]
            #aceleasi baze au acelasi foton
            if basis == original_basis:
                resulting_polarization = polarization
            else:
                #daca baza este diferita se masoara random fotonul ei, de ex. pt baza +, avem fotoni → sau ↑ cu sanse 50%
                measurement = random.randint(0, 1)
                resulting_polarization = self.polarization_map[(basis, measurement)]
            
            resulting_polarizations.append(resulting_polarization)
        
        self.current_polarizations = resulting_polarizations
        #de vreme ce current polarizations se modifica doar din receiver, verificam de fiecare data daca a intervenit eve
        self._check_eavesdropping(measurement_bases)
        return resulting_polarizations
    
    #shared key sunt practic fotonii la fel, pentru ca fara eve asta inseama baze la fel, si in caz de eve fix asta e modul in care detectam ca e posibil
    #ca daca alice are baza + si foton ↑ si eve ghiceste baza x, atunci bob avand baza + sa aiba fotonul →, ceea ce ar fi imposibil fara eve
    def extract_shared_key(self, sender_polarizations: List[str], receiver_polarizations: List[str]) -> List[int]:
        shared_key = []
        
        for i in range(len(sender_polarizations)):
            if sender_polarizations[i] == receiver_polarizations[i]:
                original_basis, bit = self.reverse_polarization_map[sender_polarizations[i]]
                shared_key.append(bit)
        
        return shared_key
    
    #cum ziceam mai sus, daca bazele lui bob si alice sunt aceleasi dar fotonii sunt diferiti, inseamna ca a intervenit eve, ca altfel e imposibil
    def _check_eavesdropping(self, receiver_bases: List[str]):
        for i in range(len(self.original_polarizations)):
            if receiver_bases[i] == self.reverse_polarization_map[self.original_polarizations[i]][0]:
                expected_polarization = self.original_polarizations[i]
                actual_polarization = self.current_polarizations[i]
                if expected_polarization != actual_polarization:
                    self.eve_detected = True
                    return
    
    def encrypt_message(self, message: str, key: List[int]) -> Optional[str]:
        if not key:
            return None
        
        message_binary = ''.join(format(ord(char), '08b') for char in message)
        key_repeated = (key * ((len(message_binary) // len(key)) + 1))[:len(message_binary)]
        
        encrypted = []
        for i in range(len(message_binary)):
            encrypted.append(str(int(message_binary[i]) ^ int(key_repeated[i])))
        
        return ''.join(encrypted)
    
    def decrypt_message(self, encrypted_message: str, key: List[int]) -> Optional[str]:
        if not key:
            return None
        
        key_repeated = (key * ((len(encrypted_message) // len(key)) + 1))[:len(encrypted_message)]
        
        decrypted = []
        for i in range(len(encrypted_message)):
            decrypted.append(str(int(encrypted_message[i]) ^ int(key_repeated[i])))
        
        decrypted_binary = ''.join(decrypted)
        
        message = ""
        for i in range(0, len(decrypted_binary), 8):
            byte = decrypted_binary[i:i+8]
            if len(byte) == 8:
                message += chr(int(byte, 2))
        
        return message


class QuantumEntity:
    
    def __init__(self, name: str, protocol: BB84Protocol):
        self.name = name
        self.protocol = protocol
        self.bits = []
        self.bases = []
        self.polarizations = []
    
    def generate_data(self, length: int = None):
        if length is None:
            length = self.protocol.key_length
        self.bits = self.protocol.generate_random_bits(length)
        self.bases = self.protocol.generate_random_bases(length)
    
    def polarize_photons(self):
        self.polarizations = self.protocol.polarize_photons(self.bits, self.bases)
    
    def measure_photons(self):
        self.polarizations = self.protocol.measure_photons(self.bases)
    
    def send_bases(self, receiver, channel):
        message = Message(self.name, receiver.name, 'bases', self.bases)
        print(f"{self.name} => bases => {receiver.name}: {self.bases}")
        channel.send_message(message)
        receiver._inbox = message
    
    def receive_bases(self, sender):
        if not hasattr(self, '_inbox') or self._inbox is None or self._inbox.message_type != 'bases':
            print(f"{self.name} Fara bases de la {sender.name}.")
            return
        print(f"{self.name} PRIMIT bases de la {sender.name}: {self._inbox.data}")
        self._inbox = None
    


class Sender(QuantumEntity):
    
    def __init__(self, protocol: BB84Protocol, name: str = "Alice"):
        super().__init__(name, protocol)
    
    def send_qubits(self, receiver, channel):
        self.generate_data()
        self.polarize_photons()
        print(f"{self.name} Bits:       {self.bits}")
        print(f"{self.name} Photons:    {self.polarizations}")
        message = Message(self.name, receiver.name, 'qubits', self.polarizations)
        channel.send_message(message)
        receiver._inbox = message
        return message
    
    def send_encrypted_message(self, receiver, channel, message: str = "BEBE GRI"):
        if self.protocol.eve_detected:
            print("EVEEEE!!!!")
            self._outbox = None
            return None
        
        print("No Eve detected")
        shared_key = self.protocol.extract_shared_key(self.polarizations, self.protocol.current_polarizations)
        encrypted = self.protocol.encrypt_message(message, shared_key)
        print(f"Msj encriptat:  {encrypted}")
        msg = Message(self.name, receiver.name, 'encrypted', encrypted)
        channel.send_message(msg)
        self._outbox = msg


class Receiver(QuantumEntity):
    
    def __init__(self, protocol: BB84Protocol, name: str = "Bob"):
        super().__init__(name, protocol)
    
    def receive_qubits(self, sender):
        if not hasattr(self, '_inbox') or self._inbox is None or self._inbox.message_type != 'qubits':
            print(f"{self.name} nu a primit qbits de la {sender.name}.")
            return
        
        print(f"{self.name} a primit qbits de la {sender.name}")
        self.generate_data()
        self.measure_photons()
        print(f"{self.name} Photoni masurati:      {self.polarizations}")
        self._inbox = None
    
    #vede daca a primit vreun mesaj de la sender
    def receive_encrypted_message(self, sender):
        if not hasattr(sender, '_outbox') or sender._outbox is None or sender._outbox.message_type != 'encrypted':
            print(f"{self.name} nu a primit mesaj de la {sender.name}.")
            return
        
        shared_key = self.protocol.extract_shared_key(self.protocol.original_polarizations, self.polarizations)
        decrypted = self.protocol.decrypt_message(sender._outbox.data, shared_key)
        print(f"{self.name} Msj decriptat:    {decrypted}")
        sender._outbox = None


def run_without_eve():
    print("------- No Eve ------------")
    
    protocol = BB84Protocol(key_length=20)
    channel = CommunicationChannel()
    alice = Sender(protocol, "Alice")
    bob = Receiver(protocol, "Bob")
    
     # in general flowul e alice trimite qbitii, apoi isi dau bazele si apoi alice trimite mesajul encriptat
    alice.send_qubits(bob, channel)
    bob.receive_qubits(alice)
    
    alice.send_bases(bob, channel)
    bob.send_bases(alice, channel)
    alice.receive_bases(bob)
    bob.receive_bases(alice)
    
    alice.send_encrypted_message(bob, channel)
    bob.receive_encrypted_message(alice)


def run_with_eve():
    print("\n------- With Eve ------------")
    
    protocol = BB84Protocol(key_length=20)
    channel = CommunicationChannel()
    alice = Sender(protocol, "Alice")
    eve = Receiver(protocol, "Eve")
    bob = Receiver(protocol, "Bob")
    
    channel.register_eavesdropper(eve)
    
    alice.send_qubits(bob, channel)
    eve.receive_qubits(alice)
    bob.receive_qubits(alice)
    
    alice.send_bases(bob, channel)
    eve.send_bases(bob, channel)
    bob.send_bases(alice, channel)
    alice.receive_bases(bob)
    bob.receive_bases(alice)
    
    alice.send_encrypted_message(bob, channel)
    bob.receive_encrypted_message(alice)


def main():    
    run_without_eve()
    run_with_eve()


if __name__ == "__main__":
    main()