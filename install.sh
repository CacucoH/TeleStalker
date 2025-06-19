mkdir logs reports session 2> /dev/null
python -m venv myenv
source myenv/bin/activate
pip3 install -r requirements.txt

[[ $? -eq 0 ]] && echo 'Congrads, installation was successful!'