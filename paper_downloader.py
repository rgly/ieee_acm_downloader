#!/usr/bin/env python3

# =============== Library Dependency ==============
from lxml import html # HTML parser, used to extract paper title
import urllib.request as urllib2 # builtin lib for IEEE html spider
import requests # for ACM html spider, I don't know why ACM & IEEE are not compatiable

# used by main
import subprocess # issuing local shell commands
import paramiko # ssh or sftp to remote machine
from pprint import pprint # builtin pretty print
from pathlib import Path # for directory creation
import re # builtin regex to match DOI


# ================== Config ====================
# The URL of the remote machine to access IEEE/ACM.
# If you are going to access IEEE/ACM locally, Set to 'localhost'.
REMOTE_PC:str='server.school.edu.tw'

# The account of the remote machine.
# Not used if REMOTE_PC is set to localhost.
USER:str='username'

# The ssh port of the remote machine.
# Not used if REMOTE_PC is set to localhost.
PORT:int=22

# The ssh key file path for the password-less login to remote machine,
# might need ssh-agent & ssh-add if ssh keys are crypted.
# Not used if REMOTE_PC is set to localhost.
KEYFILE:str=f"/home/{USER}/.ssh/id_rsa.pub"

# The directory of downloaded papers on remote server
# Not used if REMOTE_PC is set to localhost.
REMOTE_DIR:str='/where/dir/in/proxy/server'

# The directory to put downloaded papers.
LOCAL_DIR:str="local_dir"

# IEEE/ACM paper URL to be downloaded.
# arxiv is not supported.
PAPER_URLS:str = '''
https://ieeexplore.ieee.org/document/4764139
https://dl.acm.org/doi/10.1145/368453.368641
'''

# Renaming paper titles after downloaded.
# Please feel free to modify this function.
def renamePaperTitle(title:str) -> str:
  assert(len(title))

  # space -> underline
  title = title.replace(' ', '_')
  # slash -> hyphen
  title = title.replace('/', '-')

  # limit filename length
  FILE_NAME_LIMIT:int = 100
  if len(title) > FILE_NAME_LIMIT:
    title = title[0:FILE_NAME_LIMIT]

  assert(len(title))
  return title



# =============== Implementation ==============
#creating a new directory called pythondirectory
Path(LOCAL_DIR).mkdir(parents=True, exist_ok=True)

def getIEEEHtml(url:str) -> str:
  html_content = urllib2.urlopen(url).read()
  return html_content

def getACMHtml(url:str) -> str:
  r = requests.get(url)
  return r.text

def IsHttp(url:str) -> bool:
  return url[0:4] == "http"

def extractDomain(url:str) -> str:
  assert(IsHttp(url))
  domains:str = url.split('/')
  domain = domains[2]
  return domain

def IsIEEE(url:str) -> bool:
  if url.isnumeric():
    return True
  elif IsHttp(url):
    domain = extractDomain(url)
    return domain == 'ieeexplore.ieee.org'
  else:
    return False

# identify 10.1145/3549555.3549587
def IsDOI(url):
  match = re.search("^\d+\.\d+/[\w\.]+$", url)
  return match != None

def IsACM(url:str) -> bool:
  if IsDOI(url):
    return True
  elif IsHttp(url):
    domain = extractDomain(url)
    return domain == 'dl.acm.org'
  else:
    return False

def getPaperTitleFromHtml(html_content:str, UseCitationTitle:bool) -> str:
  root = html.fromstring(html_content)
  if UseCitationTitle:
    title = root.xpath('//h1[@class="citation__title"]')[0].text
  else:
    title = root.xpath('//title/text()')[0]
  # something like "Cambricon-P: A Bitflow Architecture ... | IEEE Conference Publication | IEEE Xplore" here
  # or "Deep Features for CBIR with Scarce Data using Hebbian Learning" if from citation_title

  title:str = title.split('|')[0]
  paper_title:str = title.strip()
  paper_title = renamePaperTitle(paper_title)
  return paper_title

def getACMIDfromURL(url:str) -> str:
  assert(url)
  if IsDOI(url):
    paper_id = url
  else:
    items = list(url.split('/'))
    if items[-1] == "":
      paper_id = items[-3]+'/'+items[-2]
    else:
      paper_id = items[-2]+'/'+items[-1]
  assert(len(paper_id))
  assert(IsDOI(paper_id))
  return paper_id

def getIEEEIDfromURL(url:str) -> str:
  assert(url)
  if url.isnumeric():
    paper_id = url
  else:
    items = list(url.split('/'))
    for i in [items[-1], items[-2]]:
      if i.isnumeric():
         paper_id = i
         break
  assert(len(paper_id))
  assert(paper_id.isnumeric())
  return paper_id

LocalDirPDFs = None
def IsExist(LocalFileName:str):
  def stripNonLatin(text:str):
    a = text.replace(' ', '').replace('-', '').replace('_', '')
    b = a.replace(':', '').replace('.', '').replace('/', '')
    return b

  global LocalDirPDFs
  if LocalDirPDFs == None:
    pdfs = list(Path(LOCAL_DIR).iterdir())
    LocalDirPDFs = [stripNonLatin(str(p)) for p in pdfs]

  target_pdf = stripNonLatin(LocalFileName)
  return target_pdf in LocalDirPDFs

# Download paper on remote server
def download(DownloadURL:str, RemoteFileName:str, LocalFileName:str):
  if IsExist(LocalFileName):
    print(f"{LocalFileName} existed, skip download")
    # skip if already have
    return
  if REMOTE_PC == 'localhost':
    print(f"Download {DownloadURL} -> {LocalFileName}")
    Command = f"wget \"{DownloadURL}\" --output-document={LocalFileName}"
    try:
      output = subprocess.check_output(Command, stderr=subprocess.STDOUT,
                                       shell=True, universal_newlines=True)
    except subprocess.CalledProcessError as exc:
      print("Status : FAIL", exc.returncode, exc.output)
    else:
      print("Output: \n{}\n".format(output))
    return

  print(f"Download {DownloadURL} -> {RemoteFileName} -> {LocalFileName}")
  RemoteCommand = f"wget \"{DownloadURL}\" -O {RemoteFileName}"
  print(RemoteCommand)
  ssh = paramiko.SSHClient()
  ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
  ssh.connect(hostname=REMOTE_PC, username=USER, port=PORT,  key_filename=KEYFILE)
  stdin, stdout, stderr = ssh.exec_command(RemoteCommand)
  pprint(stdout.readlines())
  pprint(stderr.readlines())

  # Download paper to local
  sftp = ssh.open_sftp()
  print(f"sftp {RemoteFileName} -> {LocalFileName}")
  sftp.get(RemoteFileName, LocalFileName)

# parse the URL rule and decide the download URL and paper title
def ParseAndDownload(url:str):
  def hyphenate(name:str) -> str:
    return name.replace('/', '-').replace('.', '-')

  def removeURLquery(url_:str) -> str:
    # remove "?casa_token=YXGSGFSDFDSF"
    return str(list(url_.split('?'))[0])

  url = removeURLquery(url)

  if IsIEEE(url):
    PaperID:str = getIEEEIDfromURL(url)
    HtmlContent:str = getIEEEHtml(f'http://ieeexplore.ieee.org/document/{PaperID}')
    DownloadURL = f'http://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&isnumber=&arnumber={PaperID}'
    UseCitationTitle = False
  elif IsACM(url):
    PaperID:str = getACMIDfromURL(url)
    HtmlContent:str = getACMHtml(f'https://dl.acm.org/doi/{PaperID}')
    DownloadURL = f'https://dl.acm.org/doi/pdf/{PaperID}'
    UseCitationTitle = True
  else:
    assert(0 and "neither IEEE or ACM")

  PaperTitle:str = getPaperTitleFromHtml(HtmlContent, UseCitationTitle)
  LocalFileName:str = f"{LOCAL_DIR}/{PaperTitle}.pdf"
  # The file name in remote server
  # I set it to paper_* for easier removing
  HyphenPaperID = hyphenate(PaperID)
  RemoteFileName:str = f"{REMOTE_DIR}/paper_{HyphenPaperID}.pdf"
  download(DownloadURL, RemoteFileName, LocalFileName)

def str2list(a:str) -> list:
  b = a.split('\n')
  c = list(filter(lambda x: len(x) > 1, b) )
  return c

def BatchDownload(urls:list):
  for url in str2list(urls):
    ParseAndDownload(url)

BatchDownload(PAPER_URLS)
