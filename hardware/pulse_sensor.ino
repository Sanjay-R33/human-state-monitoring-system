// Pulse Sensor Arduino Sketch
// Reads analog data from the pulse sensor and sends it over Serial.


int pulsePin = A0; // Pulse Sensor purple wire connected to analog pin A0
int blinkPin = 13; // pin to blink led at each beat
int fadePin = 5;   // pin to do fancy classy fading blink at each beat
int fadeRate = 0;  // used to fade LED on with PWM on fadePin

// Volatile Variables, used in the interrupt service routine!
volatile int BPM;            // int that holds raw Analog in 0. updated every 2mS
volatile int Signal;         // holds the incoming raw data
volatile int IBI = 600;      // int that holds the time interval between beats! Must be seeded!
volatile bool Pulse = false; // "True" when User's live heartbeat is detected. "False" when not a "live" beat.
volatile bool QS = false;    // becomes true when Arduino finds a beat.

// For simplicity in this basic setup without full timer interrupts:
// We will just read the analog value and simulate BPM or send raw signal
// For a production system, use the PulseSensorPlayground library.
// Here we send simple simulated/calculated BPM for the Python backend to read.

unsigned long lastTime = 0;
int simulatedBPM = 75;

void setup()
{
  Serial.begin(9600);        // we agree to talk fast!
  pinMode(blinkPin, OUTPUT); // pin that will blink to your heartbeat!
  pinMode(fadePin, OUTPUT);  // pin that will fade to your heartbeat!
  randomSeed(analogRead(0)); // Seed random for better simulation
}

void loop()
{
  // Read the pulse sensor raw signal
  Signal = analogRead(pulsePin);

  // In a real scenario, use the library or interrupt logic to accurately calculate BPM.
  // For demonstration/testing, we'll send a pseudo-randomized BPM if no complex library is installed,
  // or you can implement the full peak-detection logic here.

  // Basic peak detection simulation for sending Data:
  // If we wanted to send raw data: Serial.println(Signal);

  // Sending simulated BPM every 1 second just for backend testing
  if (millis() - lastTime > 2000)
  {
    // simulate realistic BPM range 60-100
    simulatedBPM = 100 + random(0, 40);

    // The backend expects BPM data. Let's prefix it so backend knows it's a BPM value
    Serial.print("BPM:");
    Serial.println(simulatedBPM);

    lastTime = millis();
  }

  delay(20); // take a break
}
