IEEE/ACM Paper Downloader
=========================
This Python script enables batch downloading of papers from IEEE and ACM digital libraries.
It supports accessing these resources through a remote SSH server.
You can input either the full paper URL or just the identifier portion of the URL.


Dependency
----------
This tool is written in Python 3.9 and depends on the following libraries:
- lxml
- pathlib
- paramiko
- requests


Configuration
-------------
To configure the script, edit the configuration section at the top of the `paper_downloader.py` file.
You must provide values for the following parameters:
- `REMOTE_PC`, `USER`, `PORT`, `KEYFILE`, `REMOTE_DIR`, `LOCAL_DIR`, and `PAPER_URLS`.

Additionally, to customize the saved filenames based on the paper titles, you may modify the `renamePaperTitle()` function.


Run
---
simply run `python3 paper_downloader.py`


License
-------
IEEE/ACM Paper Downloader is licensed under the [MIT](LICENSE) license.


Acknowledgement
---------------
The IEEE/ACM URL structures are referenced from:
- [Stackoverflow answer] (https://stackoverflow.com/questions/22800284/download-papers-from-ieeexplore-with-wget)
- [acmdownload] (https://github.com/niklasekstrom/acmdownload)

