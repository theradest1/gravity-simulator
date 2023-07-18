#include <iostream>
#include <list>
#include<graphics.h>
using namespace std;

class Planet{
    public:
        float mass;
        float xPos;
        float yPos;
        float xVel;
        float yVel;
        Planet(float _mass, float _xPos, float _yPos, float _xVel, float _yVel){
            mass = _mass;
            xPos = _xPos;
            yPos = _yPos;
            xVel = _xVel;
            yVel = _yVel;
        };
        void applyVelocity(float dt){
            xPos += xVel * dt;
            yPos += yVel * dt;
        };
        void addVelocity(float addedXVel, float addedYVel){
            xVel += addedXVel;
            yVel += addedYVel;
        };
};

int main() {
    cout << "START";
    const float gravConst = .00000000001;
    list<Planet> planets = {};

    for(int i = 0; i < 3; i){
        Planet newPlanet(1, 0, 0, 1, 1);
        planets.push_back(newPlanet);
    };




    return 0;
}


