import machine
import time

class Beeper:
    def __init__(self, pin=21):
        self.pin = machine.Pin(pin, machine.Pin.OUT)
        self.pwm = machine.PWM(self.pin)
        self.pwm.freq(440)  # Base frequency (A4)
        self.pwm.duty(0)
        
        self.notes = {
            "C7": 2093,
            "A7": 3520,
            "A#7": 3699,
            "B7": 3951,
            "C8": 4186,
            "C#8": 4370,
            "D8": 4699,
            "D#8": 4891,
            "E8": 5274,
        }

        self.melodies = {
            "got_key": [(self.notes["E8"], 0.1)],
            "ok": [(self.notes["A7"], 0.2), (self.notes["D8"], 0.2), (self.notes["C8"], 0.4)],
            "lock": [(self.notes["C7"], 0.3)],
            "unlock": [(self.notes["D8"], 0.3)],
            "reject": [(self.notes["C7"], 0.1), (self.notes["C7"], 0.1), (self.notes["C7"], 0.1)],
            "boot_ok": [(self.notes["E8"], 0.1), (self.notes["B7"], 0.1), (self.notes["D8"], 0.2), (self.notes["C8"], 0.2), (self.notes["A7"], 0.4)]
        }

    def play(self, duration):
        self.pwm.duty(50)
        time.sleep(duration)
        self.pwm.duty(0)

    def play_melody(self, melody_name):
        if melody_name in self.melodies:
            melody = self.melodies[melody_name]
            for note, duration in melody:
                self.pwm.freq(note)
                self.play(duration)
                time.sleep(0.05)  # Add a slight delay between notes
        else:
            print("Melody not found:", melody_name)

