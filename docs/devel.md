# Development Documentation

## gif screencast refresh

### ffcast, ffmpeg, convert

Open terminal and prepare environment:

```
$ xfce4-terminal --hide-menubar --hide-toolbar
$ sleep 20 ; docker run -d fedora bash -c "while true : ; do sleep 1 ; date ; done"
```

Record screen:

```
$ ffcast -w % ffmpeg -f x11grab -show_region 1 -framerate 20 -video_size %s -i %D+%c -codec:v huffyuv -vf crop="iw-mod(iw\\,2):ih-mod(ih\\,2)" out.avi
```

Convert to gif and optimize:

```
$ ffmpeg -ss 3 -i out.avi -t 00:00:50.00 -vf scale=720:-1 -pix_fmt rgb24 out.gif
$ convert -limit memory 1 -limit map 1 -layers Optimize out.gif out_optimised.gif
```

 * `-ss 3` — cut until second 3
 * `-t 00:00:50.00` — process until second 50
 * `-vf scale=720:-1` — resize gif to 720px (looks like a prefered GitHub size)


### byzanz

Open terminal and get terminal coords:

```
$ xwininfo
```

Record:

```
$ byzanz-record -v --delay=5 -x 164 -y 183 -w 892 -h 418 -d 25 -- out.gif
```

 * `-d` — duration

Current gifs are created with `st`, `100x30`, `Inconsolata dz` size 16.

http://unix.stackexchange.com/questions/113695/gif-screencasting-the-unix-way  
http://askubuntu.com/questions/4428/how-to-create-a-screencast
