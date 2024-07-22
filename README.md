# <p align="center">Final Project Simplon</p>

<div align="center">
  <img src="/assets/logo.png" alt="logo" style="height: 60px;"/>
</div>

## Context

In 2021, after a training course to learn the profession of web developer carried out in 2019, I continued with a training course to learn Data and AI.
After a year and a half's training and work-study in a company, we had a final project to hand in, covering everything we had learned during the course.
It's this project.

## Project

Here's how I described my project in the written report we had to hand in along with the project (which you can find [here](https://drive.google.com/file/d/1RdjjnQPOUNftO8F311IfWKYQYSuVpdlp/view?usp=sharing), in French only 🇫🇷).

> ### Introduction
> As an amateur cyclist, I use the Strava application for every ride. As a reminder, Strava is a website and mobile application used to record sporting activities via GPS. Cycling and running account for the majority of the site's activities. The application records a wealth of information on the activity performed.
> Strava also offers Premium access to its service, enabling users to benefit from even more features. One of these is the ability to define a route on a map and then export or share it. One of the main benefits of this feature is that it enables you to prepare a future outing in an unfamiliar location, and then import this file into a counter that will show you the route to follow once you're on your bike.

<div align="center">
  <img src="/assets/alpe_huez_prediction.png" alt="alpe d'huez prediction" style="height: 350px;"/>
</div>

> When you create a trail on the website, as shown in the screenshot above, Strava shows you the total distance, the positive and negative gradient, but also - and this is what interests us most in this project - the estimated travel time. At first glance, this information could be interesting for the user (for example, to know how long it will take to complete an activity, if he's short of time or doing sport in an unfamiliar region), but we soon realize that this estimate is problematic.

> ### Problematic
> The route we've used as an example represents approximately the ascent of the legendary Alpe D'Huez, one of the Tour de France's most famous climbs, with a vertical drop of 1,090 meters over a distance of just under 14 kilometers. Italian Marco Pantani (one of the best climbers in the history of cycling, sanctioned for doping in 1999 and dead of an overdose in 2004) has held the record for this climb since 1995, clocking 36min40. However, as you can see, Strava predicts an estimated travel time on the same route of just over 34 minutes. Strava therefore seems to be very much mistaken in the estimate provided to the user. Without knowing their method of calculation, we can quickly “guess” one of the problems by noticing that the application provides us with the same time for the same route in the other direction (downhill): this doesn't take into account the difference in altitude, and the estimate provided (14 km in 34 min) represents an average speed of just under 25 km/hour, which is the average speed that a relatively untrained cyclist would reach on a flat route.

>The idea of this project would be to develop an application using AI and Machine Learning to obtain a more realistic estimate of travel time during a future activity, taking into account not only the topography of the road but also previous sports outings (and therefore previous performances on similar routes). In the future, once the success of the concept has been confirmed by the production of an MVP that would make more realistic predictions than the existing one, we could also imagine aggregating other data in the training of a model (estimation of current form through various indicators, weight, equipment), sport being a very data-rich field.

 ### Technologies
 
![Technologies ](https://skillicons.dev/icons?i=py,fastapi,sklearn,js,elasticsearch,docker)


### Deployment

Create an .env file in the project root

```
STRAVA_CLIENT_ID=
STRAVA_CLIENT_SECRET=
ELASTIC_PASSWORD=
ELASTIC_SECURITY=
```

```
docker compose up --build
docker compose down
```

Go to http://localhost:8090/

## My Work

https://github.com/user-attachments/assets/f7284998-cf2b-45f1-baab-beccccd4e866
