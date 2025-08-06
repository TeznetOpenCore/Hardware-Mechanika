#include <SoftwareSerial.h>
#include <SPI.h>
#include <MFRC522.h>
#include <AccelStepper.h> // Include the AccelStepper library

// Pin definitions for MFRC522
#define RST_PIN 9      // Reset pin for MFRC522
#define SS_PIN 10      // Slave Select pin for MFRC522

// Define the motor pins
#define MP1  4 // IN1 on the ULN2003
#define MP2  5 // IN2 on the ULN2003
#define MP3  6 // IN3 on the ULN2003
#define MP4  7 // IN4 on the ULN2003

// Create instances
SoftwareSerial reyaxSerial(3, 2);  // RX, TX for Reyax 896
MFRC522 mfrc522(SS_PIN, RST_PIN); // Create MFRC522 instance

// Create stepper motor instance
#define MotorInterfaceType 8 // Define the interface type as 8 = 4 wires * step factor (2 for half step)
AccelStepper stepper = AccelStepper(MotorInterfaceType, MP1, MP3, MP2, MP4); // Define the pin sequence (IN1-IN3-IN2-IN4)
const int SPR = 2048; // Steps per revolution

// Array to store designated keys in specific slots
String keySlots[3] = {"", "", ""}; // Slots: 0 - EXX, 1 - EYX, 2 - EZX
const int maxSlots = 3; // Number of slots available

void setup() {
  Serial.begin(9600);       // Initialize hardware serial for debugging
  reyaxSerial.begin(9600);  // Initialize SoftwareSerial for Reyax 896 communication
  delay(500);               // Allow time for serial connection to establish
  
  // Initialize MFRC522
  SPI.begin();
  mfrc522.PCD_Init();

  // Initialize the stepper motor
  stepper.setMaxSpeed(1000); // Set the maximum motor speed in steps per second
  stepper.setAcceleration(230); // Set the maximum acceleration in steps per second^2

  // Reyax initialization commands
  initializeReyax();
}

void loop() {
  // Check if data is available from the Reyax 896
  if (reyaxSerial.available()) {
    String response = reyaxSerial.readString(); // Read the response
    Serial.print("Reyax response: ");
    Serial.println(response); // Print the response to the serial monitor

    // Handle the incoming message
    if (response.startsWith("+RCV=")) {
      Serial.println("Parsing LoRa message...");
      parseLoRaMessage(response);
    } else if (response.startsWith("REQUEST_REGISTERS")) {
      sendRegistersToReyax();
    }
  }
  
  // Check if a new RFID tag is detected
  if (mfrc522.PICC_IsNewCardPresent() && mfrc522.PICC_ReadCardSerial()) {
    Serial.println("Tag detected!");

    // Read the UID of the RFID tag
    String uid = "";
    for (byte i = 0; i < mfrc522.uid.size; i++) {
      uid += String(mfrc522.uid.uidByte[i] < 0x10 ? "0" : "") + String(mfrc522.uid.uidByte[i], HEX);
    }

    // Check if the UID is in one of the designated slots
    bool keyFound = false;
    for (int i = 0; i < maxSlots; i++) {
      if (keySlots[i] == uid) {
        Serial.print("Access granted: Key is designated in slot ");
        Serial.println(i == 0 ? "EXX" : (i == 1 ? "EYX" : "EZX"));
        keyFound = true;

        // Start the motor for 10 seconds
        startStepperMotorForDuration(10); // Set duration to 10 seconds
        break;
      }
    }

    if (!keyFound) {
      // Send UID to Reyax 896
      String sendCommand = "AT+SEND=0,100," + uid + "\r\n";
      reyaxSerial.print(sendCommand);
      Serial.print("Sent to Reyax: ");
      Serial.println(sendCommand);
    }

    // Halt PICC
    mfrc522.PICC_HaltA();
    // Stop encryption on PCD
    mfrc522.PCD_StopCrypto1();
  }
}

// Function to start the stepper motor for a given duration in seconds
void startStepperMotorForDuration(unsigned long duration) {
  unsigned long startTime = millis();

  // Move forward for the entire duration
  stepper.moveTo(3 * SPR); // Move to a position equivalent to 3 revolutions
  stepper.runToPosition(); // Run the motor to the target position
  
  // Wait for the duration
  while (millis() - startTime < duration * 1000) {
    // Keep the motor running
    stepper.run();
  }

  // Move back to the original position
  stepper.moveTo(-3 * SPR); // Move back to the original position
  stepper.runToPosition(); // Run the motor to the target position
}

// Function to send the contents of the registers to the other Reyax
void sendRegistersToReyax() {
  String message = "REGISTER_VALUES:";
  for (int i = 0; i < maxSlots; i++) {
    if (i > 0) {
      message += ", "; // Separate slots with commas
    }
    message += (i == 0 ? "EXX-" : (i == 1 ? "EYX-" : "EZX-")) + (keySlots[i].length() == 0 ? "EMPTY" : keySlots[i]);
  }

  // Ensure message length does not exceed 100 characters
  String truncatedMessage = message;
  if (truncatedMessage.length() > 100) {
    truncatedMessage = truncatedMessage.substring(0, 100);
  }

  // Construct the AT+SEND command with the register values
  String sendCommand = "AT+SEND=0,100," + truncatedMessage + "\r\n";
  reyaxSerial.print(sendCommand);
  Serial.print("Sent register values to Reyax: ");
  Serial.println(sendCommand);
}

// Function to parse the LoRa message and handle commands
void parseLoRaMessage(String message) {
  Serial.println("Inside parseLoRaMessage function.");
  
  message.trim(); // This removes any leading or trailing whitespace and EOL characters
  
  int startDataIndex = message.indexOf("EXX-");
  if (startDataIndex == -1) {
    startDataIndex = message.indexOf("EYX-");
  }
  if (startDataIndex == -1) {
    startDataIndex = message.indexOf("EZX-");
  }
  if (startDataIndex == -1) {
    startDataIndex = message.indexOf("remove EXX");
  }
  if (startDataIndex == -1) {
    startDataIndex = message.indexOf("remove EYX");
  }
  if (startDataIndex == -1) {
    startDataIndex = message.indexOf("remove EZX");
  }

  if (startDataIndex != -1) {
    String action;
    if (message.indexOf("EXX-") == startDataIndex) {
      action = "EXX";
      startDataIndex += strlen("EXX-");
    } else if (message.indexOf("EYX-") == startDataIndex) {
      action = "EYX";
      startDataIndex += strlen("EYX-");
    } else if (message.indexOf("EZX-") == startDataIndex) {
      action = "EZX";
      startDataIndex += strlen("EZX-");
    } else if (message.indexOf("remove EXX") == startDataIndex) {
      action = "remove EXX";
      startDataIndex += strlen("remove EXX");
    } else if (message.indexOf("remove EYX") == startDataIndex) {
      action = "remove EYX";
      startDataIndex += strlen("remove EYX");
    } else if (message.indexOf("remove EZX") == startDataIndex) {
      action = "remove EZX";
      startDataIndex += strlen("remove EZX");
    }
    int endDataIndex = message.indexOf(',', startDataIndex);
    if (endDataIndex == -1) {
      endDataIndex = message.indexOf('\r', startDataIndex);
    }
    if (endDataIndex == -1) {
      endDataIndex = message.indexOf('\n', startDataIndex);
    }
    String uid = message.substring(startDataIndex, endDataIndex);
    uid.trim();

    Serial.print("Command: ");
    Serial.println(action);

    if (action == "EXX") {
      setKeySlot(0, uid);
    } else if (action == "EYX") {
      setKeySlot(1, uid);
    } else if (action == "EZX") {
      setKeySlot(2, uid);
    } else if (action == "remove EXX") {
      clearKeySlot(0);
    } else if (action == "remove EYX") {
      clearKeySlot(1);
    } else if (action == "remove EZX") {
      clearKeySlot(2);
    } else {
      Serial.println("Unknown command.");
    }

    // Send acknowledgment via LoRa
    sendAcknowledgment(uid + " processed in slot " + action);
    sendRegistersToReyax();
  } else {
    Serial.println("Data does not contain a recognizable command.");
  }
}

// Function to set a key in a specific slot
void setKeySlot(int slot, String uid) {
  if (slot >= 0 && slot < maxSlots) {
    keySlots[slot] = uid;
  }
}

// Function to clear a key from a specific slot
void clearKeySlot(int slot) {
  if (slot >= 0 && slot < maxSlots) {
    keySlots[slot] = "";
  }
}

// Function to send acknowledgment via LoRa
void sendAcknowledgment(String message) {
  String sendCommand = "AT+SEND=0,100," + message + "\r\n";
  reyaxSerial.print(sendCommand);
  Serial.print("Sent acknowledgment to Reyax: ");
  Serial.println(sendCommand);
}

// Function to initialize Reyax settings
void initializeReyax() {
  reyaxSerial.println("AT+BAND?");  // Sending a basic AT command
  delay(2000);
  reyaxSerial.println("AT+CPIN?");
  delay(2000); 
  reyaxSerial.println("AT+NETWORKID=13");
  delay(2000);
  reyaxSerial.println("AT+NETWORKID?");
  delay(2000);
  reyaxSerial.println("AT+ADDRESS=111");
  delay(2000);
  reyaxSerial.println("AT+ADDRESS?");
  delay(2000);
}
