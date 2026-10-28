# USAGE


## Model Generator

Well... The Model Generator menu isn't functional yet... BUT! I CAN TEACH YOU HOW TO MAKE A MODEL YOURSELF!

Create a `setup.yaml` file that contains:

```yaml
sprite:
  size: 128
  bob:
    speed: 0.06
    height: 6
  shadow:
    height: 18

anim:
  idle:
    directory: #DIR
```

You can change all of the sprite settings around to your liking. Replace #DIR with the location to the idle .gif in your current directory.

Package all those files into a .zip and change the filetype to .oemf (yes, those are just zips) and voilla! Your own model! Now just dump it into your Okulo models folder and you can load it in with the Config Editor!


## Config Editor

The config editor has three fields:
* Model Archive
* Config Editor Icon
* Model Generator Icon

Model Archive decides the model to be used by Okulo (on how to make one, reffer to the Model Generator section).

Config Editor Icon and Model Generator Icon (supports .ico, .png, .jpg, .jpeg and .svg) decide on the icon to be used by those menus.