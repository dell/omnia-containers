# xcat2.github.io

## Quick start steps to modify index.html

index.html is common html, you can customize anything, this is a quick start to replace the content.

Assume you have forked master branch and created new branch named ``base_line``, you want to upload ``xCAT introduction video`` and change ``user scenarios`` for the ``index.html`` in your Macbook.

### Upload new ``xCAT introduction video``

1. Git clone ``base_line`` branch to your Macbook 
```
git clone -b base_line https://github.com/bybai/xcat2.github.io.git
```
2. Copy new video ``introduction.mp4`` into ``xcat2.github.io.git/webcontent/assets`` directory to replace old video ``power9.mov``.
```
cp introduction.mp4 xcat2.github.io.git/webcontent/assets
git add introduction.mp4
git rm power9.mov
```
3. Edit ``index.html``, and find ``power9.mov``, change it as ``introduction.mp4``, save the page

4. Use ``firefox`` browser in your Macbook to open ``index.html`` to check the results

### Change ``user scenarios`` text content

1. Copy the text "Top 1 and 2 High performance computing" from ``firefox`` browser ``index.html``, open the ``index.html`` using ``vim``, find "Top 1 and 2 High performance computing" and edit it, save the page
```
vim index.html
git add index.html
```
2. Use ``firefox`` browser in your Macbook to open ``index.html`` to check the results

### Use ``git`` to commit and push your results to your own branch
```
git diff --cached
git commit -a -m "update ..."
git push
```
