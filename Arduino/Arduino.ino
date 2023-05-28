#include <OneWire.h>
#include <DallasTemperature.h>

// PWM PINs 
#define FIR_PIN 6
#define NIR_PIN 5
#define VIS_PIN 3
#define UV_PIN 9

// TEMP PINs
//If all temp are on same pins change code 
#define TEMP_PIN 4

#define ARDUINO_NUM 1
#define MAX_TEMP 80 

#define BAUD_RATE 9600
#define N 50

// Global variables 
int currentFIR=0, currentNIR=0, currentVIS=0, currentUV=0; 

OneWire oneWire(TEMP_PIN);
DallasTemperature sensors(&oneWire);

void setup()
{  
  // Set PWM pins as output 
  pinMode(FIR_PIN, OUTPUT);
  pinMode(NIR_PIN, OUTPUT);
  pinMode(VIS_PIN, OUTPUT);
  pinMode(UV_PIN, OUTPUT);  

  // Set PWM pins to 0
  analogWrite(UV_PIN, 0);  
  analogWrite(NIR_PIN, 0); 
  analogWrite(VIS_PIN, 0); 
  analogWrite(UV_PIN, 0);
   
  // Begin serial communication
  Serial.begin(BAUD_RATE); 

  // Tempeature sensor init
  sensors.begin();
}


void loop()
{  
  if (Serial.available())
  {           
    char startChar = '<';
    char endChar = '>';   

    char receivedChar = Serial.read(); 

    if (receivedChar == startChar) 
    {
      // Assuming all contents terminate with '>' if not BOOM
      String content = Serial.readStringUntil(endChar);

      String contents[N];         
      if (content.length() > N) return;   

      int index = 0; 
      String substring; 
      for (auto& c : content)
      {        
        if (c == ',')
        {           
          ++index;
          substring = String(); 
          continue; 
        } 
        substring += c;     
        contents[index] = substring;    
      }

      // Perform orders based on command
      String command = contents[0]; 
      auto panel_number = contents[1].toInt(); 

      // Is this message for me? 
      if (panel_number != ARDUINO_NUM) return;       

      String outgoingMessage = "<status,";

      if (command == "get")
      {
        // Send back current PWM signals and temperature read 
        constructMessage(outgoingMessage);       
      }
      else if(command == "set")
      {
        // Set PWM signals
        setPWMsignals(contents[2].toInt(), contents[3].toInt(), contents[4].toInt(), contents[5].toInt());
        // Send back current PWM signals and temperature read 
        constructMessage(outgoingMessage);
      } 
      else
      {
        // Error handling or different cases 
      }

      // Send the message
      Serial.println(outgoingMessage);       
    }      
    else
    {
      //Error when reciving data... Flushing input buffer 
      while(Serial.available() && endChar != Serial.read());      
    }
  }  

  // Request read temperature 
  sensors.requestTemperatures(); 

  // If temp gets too high shut down 
  if (sensors.getTempCByIndex(0) > MAX_TEMP) 
  {
    setPWMsignals(0,0,0,0); 
  } 

}


void constructMessage(String& message)
{ 
  // Get temperature
  int temp = static_cast<int>(sensors.getTempCByIndex(0)); 
  // Add panel_number as well as all current values of PWM signals  
  message += String(ARDUINO_NUM) + "," + String(currentFIR) + "," + String(currentNIR) + "," + String(currentVIS) + "," + String(currentUV) + ",";
  // Add temperatures 
  message += String(temp) + "," + String(temp) + "," + String(temp); 
  // Add closing bracket seperated by comma 
  message += ",>"; 
}


// Map values from [0, 100] to [0, 255]
void setPWMsignals(int fir, int nir, int vis, int uv)
{
  // Update global variables 
  currentFIR = fir; 
  currentNIR = nir;
  currentVIS = vis; 
  currentUV = uv; 

  analogWrite(FIR_PIN, map(fir, 0, 100, 0, 255));
  analogWrite(NIR_PIN, map(nir, 0, 100, 0, 255));
  analogWrite(VIS_PIN, map(vis, 0, 100, 0, 255)); 
  analogWrite(UV_PIN, map(uv, 0, 100, 0, 255)); 
}
