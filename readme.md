# Environmental Air Quality Box
3D-Printed Files can be found [on Thingiverse here](https://www.thingiverse.com/thing:6655576).

## Calculating Absolute Humidity from Relative Humidity and Temperature
All formulas, from [here](https://carnotcycle.wordpress.com/2012/08/04/how-to-convert-relative-humidity-to-absolute-humidity/):

![formulas](https://i.imgur.com/1aRPvRh.png)

Temperature is in Celsius, Relative Humidity as a percentage.

You can express the formula above as a Dataverse Formula column like so:
```
(6.112 * (2.71828^((17.67*(('Temperature, Fahrenheit'-32)*(5/9)))/((('Temperature, Fahrenheit'-32)*(5/9))+243.5))) * 'Relative Humidity' * 2.1674) / (273.15 + (('Temperature, Fahrenheit'-32)*(5/9)))
```