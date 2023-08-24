import requests
import logging
import re
import argparse
import sys

parser = argparse.ArgumentParser(
	prog="Z-Downloader",
	description="Download payslip from Zucchetti platform"
	)

parser.add_argument("username", help="Zucchetti username")
parser.add_argument("password", help="Zucchetti password")
parser.add_argument("org", help="Organization, first element of the URI (i.e., saas.zucchetti.it/<organization>/))")


hostbase = "https://saas.hrzucchetti.it"

headers = {
    	"Content-Type": "application/x-www-form-urlencoded",
}


logging.basicConfig(format='[%(asctime)s]: %(message)s', level = logging.INFO)


session = requests.session()

def login(username, password, org):

	url = f"{hostbase}/{org}/servlet/cp_login"
	
	data = {
		"m_cUserName" : username,
		"m_cPassword" : password,
		"m_cOTP" : "",
		"wSHOWSENDMYPWD" : "true",
		"mylink" : "",
		"m_cFailedLoginReason" : "",
		"ssotrust" : "",
		"GWINLOGON" : "",
		"g_codute" : "0.0",
		"m_cAction" : "login",
		"m_cURL" : "",
		"m_cURLOnError" : "jsp/login.jsp",
		"m_cForceLogin" : "",
		"w_FirstCodAzi" : "001",
		"g_UserCode" : "-1",
		"g_UserName" : "",
		"ssoStatus" : "0",
		"m_cInstance" : "",
		"m_cCaptcha" : "",
		"g_codazi" : "001",
		"Nodes" : "",
		"memo" : "",
		"TITOLO" : "",
		"GLOGOLGINURL" : "",
		"ERM_GANVERATT" : "230000",
		"mylang" : "",
		"browserlang" : "",
		"GLOGOLOGIN" : "",
		"g_UserLang" : "",
		"GLANGUAGEINSTALL" : "",
		"GFLSENDMYPWD" : "S",
		"GERMNAME" : "HRPortal",
		"GLOGINTITLECO" : "",
		"GIDLANGUAGE" : "ITA",
		"GLOGOFOOTER" : "",
		"GOTPLOGIN" : "0",
		"GCUSTOMLOGS" : "",
		"GANLOGINM01" : "",
		"GANLOGINM02" : "",
		"GANLOGINM03" : "",
		"Warning" : "",
		"w_Modal" : "N",
		"error" : "0",
		"FLLICENSECF" : "KO"
	}

	r = session.post(url, data=data, headers=headers, allow_redirects=False)

	if r.status_code == 302 and r.headers.get("Location") == f"../../{org}/servlet/../jsp/home.jsp":
		logging.info(f"Authentication succesful for user {username}")
		return True

	logging.error("Authentication failed - Check username and password")
	return False


def downloadDocuments(org):

	url = f"{hostbase}/{org}/jsp/ushp_one_column_model.jsp"

	m_cID = None
	cmdhash = None

	data = {
		"containerCode" : "MYDESK",
		"currentPageCode" : "1961",
		"currentPageType" : "C",
		"currentPageOwner" : "12",
		"currentAssocRow" : "3",
		"currentAllowedUser" : "0",
		"currentUserAssoc" : "0",
		"currentPageName" : "MySpace",
		"flpagehr" : "S",
		"SPParentObjId" : "",
		"PageletId" : "",
		"containerCode" : "MYDESK",
		"pTitle" : "My+Workspace",
		"SPParentObjId" : "",
		"PageletId" : "",
		"m_cParameterCache" : "",
		"clientsideinclusion" : "true"
	}

	r = session.post(url,data=data,headers=headers)

	if r.status_code == 200:
		res = re.findall(r"this.splinker7.m_cID='([a-z0-9]+)';",r.content.decode())
		m_cID = res and res[0] or None
		res = re.findall(r'"ushp_qfolderemsel_noread","cmdHash":"([a-z0-9]+)"',r.content.decode())
		cmdhash = res and res[0] or None

	if m_cID == None or cmdhash == None:
		logger.error("Something wrong happened when retrieveing m_cID and cmdhash. Aborting")
		return

	url = f"{hostbase}/{org}/servlet/SQLDataProviderServer"

	data = {
		"rows" : "1000",
		"startrow" : "0",
		"count" : "false",
		"cmdhash" : cmdhash,
		"sqlcmd" : "ushp_qfolderemsel_noread",
		"isclientdb" : "false",
		"orderby" : "chkread, dtstartview desc, LOGICFOLDERPATH",
		"pFLVIEWNG" : "S"
	}

	r = session.post(url, data=data, headers=headers)

	if r.status_code == 200:
		sqlData = r.json()

	data = {
		"idfolder" : "",
		"codepin" : "",
		"pMODE" : "inline",
		"datetocache" : "",
		"m_cAction" : "start",
		"m_cParameterSequence" : "idfolder,codepin,pMODE,datetocache",
		"m_cMode" : "hyperlink",
		"m_cID" : m_cID,
		"m_cAtExit" : "close"
	}
	
	url = f"{hostbase}/{org}/servlet/ushp_bexecdoc"
	
	for x in sqlData["Data"][0:-1]:
		logging.info(f"Downloading document \"{x[1]}\"")
		with open(f"{x[1].replace(' ','_')}.pdf","wb") as fp:
			data.update({"idfolder" : x[0]})
			r = session.post(url, data=data, headers=headers)
			if r.status_code == 200:
				fp.write(r.content)
				file_size = len(r.content) 
		logging.info(f"Status code {r.status_code}, ID \"{x[0]}\",Size: {file_size}, Document \"{x[1]}\" ")


if __name__ == "__main__":

	args = parser.parse_args()

	if login(args.username,args.password, args.org):
		downloadDocuments(args.org)
