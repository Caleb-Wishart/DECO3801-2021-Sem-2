# Guides
## Index
Part 1: Connecting to the UQCloud

Part 2: Mounting via SSHFS (Optional)

Part 3: Updating the project code

Part 4: Debugging errors
___
## Part 1: Connecting to the UQCloud


1. Add the config file

   To add the config file you can find on the github to your `.ssh` directiory (or if the config file already exists append the rules)

   Replace `YourUsername` with your student number and
   `path/to/id_rsa_[moss/deco]` with the file path

   To begin with comment out the lines starting with `IdentityFile`. To add a comment to a config file add a `#` as the first character.

   For example

   ```bash
   Host moss
      HostName moss.labs.eait.uq.edu.au
      #  IdentityFile "path/to/id_rsa_moss"
      User YourUsername
      Port 22
   ```
2. Create the SSH keys (If you don't already have one)

   ```bash
   ssh-keygen -t rsa -b 4096 -f /path/to/id_rsa_moss
   ssh-keygen -t rsa -b 4096 -f /path/to/id_rsa_deco
   ```
   The above commands will prompt you to add a passcode, you will have to enter this each time unless you leave it blank

3. Add the SSH keys to the remove servers

   ```bash
   ssh-copy-id -i /path/to/id_rsa_moss moss
   # the moss rule here is reading from the ssh config file
   ```
   If you have not connected to this host before it will ask you if you want to add it to the known hosts, type 'yes'
   ```bash
   ssh-copy-id -i /path/to/id_rsa_deco deco3801
   # the deco3801 rule here is reading from the ssh config file
   ```
4. Test using the ssh keys

   Uncomment the comments that you added in step 1.

   For example the moss rules should be

   ```bash
   Host moss
      HostName moss.labs.eait.uq.edu.au
      IdentityFile "path/to/id_rsa_moss"
      User YourUsername
      Port 22
   ```
5. Connect to the UQCloud

   ```bash
   ssh deco3801
   ```
   
___
## Part 2: Mounting via SSHFS

Instead of changing code via SSH you can mount the remote file system locally using SSHFS.


The following line will mount moss to a local folder called MOSS under the home directory.

`sudo sshfs -o allow_other,default_permissions -o IdentityFile=~/.ssh/id_rsa_moss moss:/home/students/sxxxxxxx ~/MOSS`

Note that here we are using the same identity file and SSH config shortcut that we defined in Part 1.
___
## Part 3: Updating the project code

The live project code can be found in the `/var/www/uwsgi` directory.

However, if there are major changes consider working on a branch that you checkout in your home directory (or on your local machine).
```bash
git clone https://github.com/Caleb-Wishart/DECO3801-2021-Sem-2.git
```

The code source files can either be edtied via the command line using vim or connected to using an IDE through SSH.

 ([VS Code](https://code.visualstudio.com/docs/remote/ssh) has a nice extention for this but other IDE's are also fine)

Once saved code can be commited using the normal command line git commands (or the IDE)

To update the running webpage to the latest version on the repository (main branch) do the following commands.
```bash
git pull
sudo refresh
```
___
## Part 4: Debugging errors

The following commands are available system wide
```bash
refresh     # refresh the contents of the web page
cconfig     # check the configuration of the website. Useful to debug ERROR 500 INTERNAL SERVER ERROR
log         # open the UWSGI log in less
gpid        # get the PID of the UWSGI parent process
```
