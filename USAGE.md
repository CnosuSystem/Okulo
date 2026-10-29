# USAGE


## Model Generator

Well... The Model Generator menu isn't functional yet... BUT! I CAN TEACH YOU HOW TO MAKE A MODEL YOURSELF!

Create a `setup.yaml` file. You can base yourself on the Okulo one:

```yaml
sprite:
  size: 128
  bob:
    speed: 0.06
    height: 6
  shadow:
    enabled: True
    height: 18

anim:
  idle:
    directory: sprites/idle.gif
  sleep:
    enabled: True
    wait: 60
    directory: sprites/sleep.gif
```

You can change all of the sprite settings around to your liking.
* `sprite.size` decides on... We'll, the size of the sprite.
* `sprite.bob.speed` decides on the speed of the bobbing animation.
* `sprite.bob.height` decides on how high the character travels during the bobbing animation.
* `sprite.shadow.enabled` decides on if it should draw the shadow.
* `sprite.shadow.height` decides on how high the shadow is located.
* `anim.sleep.enabled` decides on if the sleep animation even exists. If `anim.sleep` doesn't exist, it just routes it to False anyway.
* `anim.sleep.wait` decides on how much time it takes before your character goes to sleep

Replace The directories with the locations to the gifs in your current directory.

Package all those files into a .zip and change the filetype to .oemf (yes, those are just zips) and voilla! Your own model! Now just dump it into your Okulo models folder and you can load it in with the Config Editor!


## Config Editor

The config editor has three fields:
* Model Archive
* Config Editor Icon
* Model Generator Icon

Model Archive decides the model to be used by Okulo (on how to make one, reffer to the Model Generator section).

Config Editor Icon and Model Generator Icon (supports .ico, .png, .jpg, .jpeg and .svg) decide on the icon to be used by those menus.