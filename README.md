BrickLink Wanted List Export
============================

The [BrickLink website](http://www.bricklink.com/), where you can buy and sell 
LEGO parts, sets and minifigures, lacks the ability to export your wanted lists. 

This application generates a 
[BrickLink XML file](http://www.bricklink.com/help.asp?helpID=207) for any of 
your wanted lists, to be used in other applications or the BrickLink wanted list
upload page. Unlike some userscripts, the generated XML file will contain all
items from all pages of every item type (sets, parts, instructions, etc) within
your wanted list.


bricklink-export is written in [Python](http://www.python.org/).

*This application and its author are in no way affiliated with BrickLink 
Limited.*


Requirements
------------

* Python 2.6+
* [Requests](http://www.python-requests.org/)
* [pyQuery](https://pythonhosted.org/pyquery/)


Installation
------------

On most UNIX-like systems, you can install bricklink-export by running one of 
the following install commands as root or by using sudo.

``` sh
git clone git://github.com/fdev/bricklink-export.git
cd bricklink-export
python setup.py install
```

*or*

``` sh
pip install git+http://github.com/fdev/bricklink-export
```

Configuration (optional)
------------------------

It is possible to specify a default username and/or password to be used by
bricklink-export. The configuration file should be 
`$HOME/.bricklink-export.conf` or `%USERDIR%/bricklink-export.ini` and contain
the following:

```ini
[user]
username=your_username
password=your_password
```


Usage
-----

```
usage: bricklink-export [-h] [--version] [-v] [-u USERNAME] [-p PASSWORD] [-l] 
                   [-c] [-e ID]

Export a BrickLink wanted list.

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -v, --verbose         be verbose
  -u USERNAME, --username USERNAME
                        username on BrickLink
  -p PASSWORD, --password PASSWORD
                        password on BrickLink (omit for prompt)
  -l, --list            list of wanted lists
  -c, --colors          list of colors
  -e ID, --export ID    wanted list to export
  -w ID, --wanted ID    override wanted list id in export
```


Example
--------

```
$ bricklink-export -l
ID      Items    Name
0       13       Main
546727  109      Firestation
502648  8        Minifigure wishlist
510899  34       Nice to have
$ bricklink-export -e 510899 -u myusername
<INVENTORY>
  <ITEM>
    <ITEMTYPE>S</ITEMTYPE>
    <ITEMID>4719-1</ITEMID>
    <CONDITION>X</CONDITION>
    <MINQTY>2</MINQTY>
    <REMARKS></REMARKS>
    <NOTIFY>Y</NOTIFY>
    <WANTEDLISTID>510899</WANTEDLISTID>
  </ITEM>
  <ITEM>
    <ITEMTYPE>P</ITEMTYPE>
    <ITEMID>3626b</ITEMID>
    <COLOR>88</COLOR>
    <CONDITION>X</CONDITION>
    <REMARKS></REMARKS>
    <NOTIFY>N</NOTIFY>
    <WANTEDLISTID>510899</WANTEDLISTID>
  </ITEM>
...
  <ITEM>
    <ITEMTYPE>I</ITEMTYPE>
    <ITEMID>4719-1</ITEMID>
    <CONDITION>X</CONDITION>
    <MAXPRICE>5.00</MAXPRICE>
    <REMARKS></REMARKS>
    <NOTIFY>N</NOTIFY>
    <WANTEDLISTID>510899</WANTEDLISTID>
  </ITEM>
</INVENTORY>
```

