class CapacitiveMouse {
  public:
    CapacitiveSensor* sensor;
    bool keyReleased = true;
    char key;
    unsigned int releaseDelay = 20;
    unsigned int releaseTimer;
    unsigned int treshold;  
    int led;
    unsigned int sample;
    unsigned char ledBrightness;
    CapacitiveMouse(uint8_t sendPin, uint8_t receivePin, int statusLED, unsigned int capacitiveTreshold, char leftRight, unsigned char ledBrightness)  {
      sensor = new CapacitiveSensor(sendPin, receivePin);
      treshold = capacitiveTreshold;
      key = leftRight;
      led = statusLED;
      pinMode(led, OUTPUT);
    }
    ~CapacitiveMouse() {
      delete sensor;
    }
    void keyUpdate(bool mouseActive) {
      sample = sensor->capacitiveSensorRaw(1);
      if (sample > treshold) {
        if (keyReleased) {
          analogWrite(led, 255);
          if (mouseActive) Mouse.press(key);
          keyReleased = false;
        }
        releaseTimer = releaseDelay;
      }
      else {
        if (!keyReleased) {
          if (releaseTimer == 0) {
            analogWrite(led, 0);
            Mouse.release(key);
            keyReleased = true;
          }
          else {
            releaseTimer--;
          }
        }
      }
    }
};
