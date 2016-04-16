# GPhotoFrame - A Photo Frame Gadget for the GNOME Desktop.

## About

It shows pictures from:

- Local folders
- F-Spot database
- Shotwell database
- Facebook API
- Flickr API
- Tumblr API
- Picasa Web Album API
- Haikyo Clock
- RSS

## Installation

### Depends

- Python: 2.6 or 2.7
- python-gobject
- gir1.2-gtk-3.0
- gir1.2-webkit-3.0
- Twisted: twisted.internet & twisted.web
- PyXDG: except v.0.16 which has a bug

- Python-Distutils-Extra: for installation
- gnome-doc-utils: for help documentation
- pkg-config: for help documentation

### Recommends

- feedparser: for RSS plugin
- python-libproxy: for Gnome Proxy Settings
- gir1.2-gtkclutter-1.0
- gir1.2-champlain-0.12: for Photo Map

### Suggests

- python-numpy: for RSS plugin
- jQuery: for photo history html

### Installation

The gschema file must be installed.
```
  sudo cp ./share/com.googlecode.gphotoframe.gschema.xml.in /usr/share/glib-2.0/schemas/com.googlecode.gphotoframe.gschema.xml
  sudo sudo glib-compile-schemas /usr/share/glib-2.0/schemas
```
You can install with the setup script.
```
  sudo python ./setup.py install --force
```
Or, you can launch without installation. (Some functions are restricted.)
```
  ./gphotoframe
```
