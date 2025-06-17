mkdir logs reports session 2> /dev/null
pip3 install -r requirements.txt

[[ $? -eq 0 ]] && echo 'Congrads, installation was successful!'