# gettext-gen

## Usage:
```
gen_localization.py [-h] [-t]
  -h, --help       show this help message and exit
  -t, --translate  Whether or not to auto-translate missing fields
  -c, --config     Creates default .env
```

When you download this, rename `.env.example` to `.env` and then modify it to your choosing.  
Most options can be modified in the `.env` file, but in order to change the files `xgettext` scans, you will need to modify the `files` list in the python file.

## Requirements
You will need to have the following in your path:  
- xgettext
- msgfmt
- msginit
- msgmerge  

You can get these for both Linux and Windows.  
On Linux, use your package manager.  
On Windows, you can get it from quite a few places, here's one: https://gnuwin32.sourceforge.net/packages/gettext.htm

## Automatic Translation
Add the following to your `.env` file:
```
DEEPL_KEY=YOUR_KEY_HERE
```
Once done, you can run the script with `-t` or `--translate`.  
Note: It will only translate fields that haven't already been translated. If you would like to have it translate again, clear the `msgstr` so it looks like: `msgstr ""`

## Manual Translation
To manually translate, just edit the `.po` files and then run the script again. It will build it and move the built files to their correct locations.

---

## Notices
It throws warnings if you do something like:
```cpp
gettext("Hello World!\n");
```
Don't add newlines like this for now, even though I think it still works.  
I recommend doing the following:
```cpp
#define STR_MYTEXT _("My Text")
```