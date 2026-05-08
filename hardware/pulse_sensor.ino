#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// =========================
// Pulse Sensor
// =========================
int pulsePin = A0;
int signal = 0;

// =========================
// BPM Variables
// =========================
int threshold = 560;   // Adjust if needed
unsigned long lastBeatTime = 0;

int BPM = 0;
int avgBPM = 0;

bool beatDetected = false;

// =========================
// BPM Averaging
// =========================
#define RATE_SIZE 10

int rates[RATE_SIZE];
int rateSpot = 0;

// =========================
// OLED Graph Buffer
// =========================
int graph[128];

void setup() {

  Serial.begin(9600);

  // OLED initialization
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("OLED failed");
    while (1);
  }

  display.clearDisplay();
  display.setTextColor(WHITE);

  // Initialize graph
  for (int i = 0; i < 128; i++) {
    graph[i] = 32;
  }

  // Initialize BPM array
  for (int i = 0; i < RATE_SIZE; i++) {
    rates[i] = 0;
  }
}

void loop() {

  // =========================
  // Smooth Sensor Reading
  // =========================
  long sum = 0;

  for (int i = 0; i < 5; i++) {
    sum += analogRead(pulsePin);
    delay(2);
  }

  signal = sum / 5;

  // =========================
  // Heartbeat Detection
  // =========================
  if (signal > threshold && !beatDetected) {

    beatDetected = true;

    // Ignore fake fast beats
    if (millis() - lastBeatTime > 450) {

      unsigned long delta = millis() - lastBeatTime;
      lastBeatTime = millis();

      BPM = 60000 / delta;

      // Accept only realistic BPM range
      if (BPM > 45 && BPM < 130) {

        rates[rateSpot++] = BPM;
        rateSpot %= RATE_SIZE;

        // Calculate average BPM
        int total = 0;
        int count = 0;

        for (int i = 0; i < RATE_SIZE; i++) {

          if (rates[i] > 0) {
            total += rates[i];
            count++;
          }
        }

        if (count > 0) {
          avgBPM = total / count;
        }
      }
    }
  }

  // Reset beat detection
  if (signal < threshold - 20) {
    beatDetected = false;
  }

  // =========================
  // Send Data to Software
  // =========================
  if (avgBPM > 0) {
    Serial.print("BPM:");
    Serial.println(avgBPM);
  }

  // =========================
  // Update Graph
  // =========================

  // Shift graph left
  for (int i = 0; i < 127; i++) {
    graph[i] = graph[i + 1];
  }

  // Convert signal to OLED height
  int y = map(signal, 450, 750, 63, 0);

  y = constrain(y, 0, 63);

  graph[127] = y;

  // =========================
  // OLED Display
  // =========================
  display.clearDisplay();

  // Draw waveform
  for (int x = 0; x < 127; x++) {
    display.drawLine(x, graph[x], x + 1, graph[x + 1], WHITE);
  }

  // Display BPM
  display.setTextSize(1);

  display.setCursor(0, 0);
  // display.print("BPM: ");
  // display.print(BPM);

  display.setCursor(0, 10);
  display.print("BPM: ");
  display.print(avgBPM);

  display.display();

  delay(20);
}
