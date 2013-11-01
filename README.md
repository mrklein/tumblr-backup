# tumblr-backup

Simple script for creating Tubmrl blog backup.

Currently supports only photo posts and basically just downloads photos from
blog and liked photos of the blog.

Usage:

`tumblr-backup.py [-l / --likes] [-d / --destination] <blog address>`

Using `-l` flag it is possible to create backup of likes of the blog. With `-d`
flag you can set the destination directory for backup. If omitted backup will
be created in current folder.

MIT License
