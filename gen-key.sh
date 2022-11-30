#!/bin/sh

cd ~/.ssh;
echo " ../(. _. ) Write file name what you want to make after first question .. \n\n"
ssh-keygen -t rsa

echo "\n\n Done!! check your passphrase and paste on it to github settings (^^)b"
echo "$ cat ~/.ssh/***.pub"