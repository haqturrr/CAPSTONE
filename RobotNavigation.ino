#include "CytronMotorDriver.h"
#define DEADZONE 300


// Configure the motor driver.
CytronMD motor1(PWM_PWM, 13, 12);
CytronMD motor2(PWM_PWM, 32, 33); 
CytronMD motor3(PWM_PWM, 14, 27);
CytronMD motor4(PWM_PWM, 25, 26);

const int xAxisPin = 4; 
const int yAxisPin = 35; 

int CENTER = 1050;


void leftMotorsForward() {

    motor1.setSpeed(100);
    motor3.setSpeed(100);

}

void rightMotorsForward() {

    motor2.setSpeed(100);
    motor4.setSpeed(100);

}

void leftMotorsBackward() {

    motor1.setSpeed(-100);
    motor3.setSpeed(-100);

}

void rightMotorsBackward() {

    motor2.setSpeed(-100);
    motor4.setSpeed(-100);

}

void stopAllMotors() {

  motor1.setSpeed(0);
  motor2.setSpeed(0);
  motor3.setSpeed(0);
  motor4.setSpeed(0);

}


// The setup routine runs once when you press reset.
void setup() {
  
stopAllMotors();

}


// The loop routine runs over and over again forever.
void loop() {

int xPosition = analogRead(xAxisPin);
int yPosition = analogRead(yAxisPin);

int xDiff = xPosition - CENTER;
int yDiff = yPosition - CENTER;



  bool yCentered = abs(yDiff) < DEADZONE;
  bool xCentered = abs(xDiff) < DEADZONE;

if (!yCentered){

  if (yDiff> DEADZONE)
  {
    leftMotorsForward();
    rightMotorsForward();
  }

  else if (yDiff < -DEADZONE)
  {
    leftMotorsBackward();
    rightMotorsBackward();
  }

}

else if(!xCentered){
  if (xDiff > DEADZONE)
  {
    rightMotorsBackward();
    leftMotorsForward();
  }

  else if (xDiff < -DEADZONE)
  {
    leftMotorsBackward();
    rightMotorsForward();
  }
}
  else 
  {
    stopAllMotors();
  }

delay(50);

}
