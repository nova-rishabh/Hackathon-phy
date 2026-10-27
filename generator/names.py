"""Small built-in name lists: (Devanagari, Latin). Synthetic; no real people."""
MALE = [("रमेश","Ramesh"),("सुरेश","Suresh"),("महेश","Mahesh"),("दिनेश","Dinesh"),("राजेश","Rajesh"),
 ("मुकेश","Mukesh"),("अनिल","Anil"),("सुनील","Sunil"),("विजय","Vijay"),("संजय","Sanjay"),("अजय","Ajay"),
 ("अमित","Amit"),("राकेश","Rakesh"),("मनोज","Manoj"),("प्रदीप","Pradeep"),("सतीश","Satish"),("हरि","Hari"),
 ("गोविंद","Govind"),("किशन","Kishan"),("मोहन","Mohan"),("श्याम","Shyam"),("राम","Ram"),("लक्ष्मण","Laxman"),
 ("भूपेंद्र","Bhupendra"),("जसवंत","Jaswant"),("बलविंदर","Balwinder"),("गुरप्रीत","Gurpreet"),
 ("हरप्रीत","Harpreet"),("सुखदेव","Sukhdev"),("परमजीत","Paramjit"),("अमरजीत","Amarjit"),("कुलदीप","Kuldeep"),
 ("जगदीश","Jagdish"),("देवेंद्र","Devendra"),("नरेश","Naresh"),("वीरेंद्र","Virendra"),("धर्मपाल","Dharampal"),
 ("बलराम","Balram"),("तरसेम","Tarsem"),("शिवम","Shivam")]
FEMALE = [("सुनीता","Sunita"),("मीना","Meena"),("कमला","Kamla"),("सीता","Sita"),("गीता","Geeta"),("रेखा","Rekha"),
 ("सरिता","Sarita"),("अनीता","Anita"),("पूजा","Pooja"),("सुमन","Suman"),("मंजू","Manju"),("कविता","Kavita"),
 ("ममता","Mamta"),("शांति","Shanti"),("राधा","Radha"),("लक्ष्मी","Laxmi"),("सावित्री","Savitri"),
 ("पार्वती","Parvati"),("कुसुम","Kusum"),("बीना","Beena"),("नीलम","Neelam"),("सुषमा","Sushma"),("ऊषा","Usha"),
 ("आशा","Asha"),("रानी","Rani"),("किरण","Kiran"),("जसविंदर","Jaswinder"),("मनप्रीत","Manpreet"),
 ("गुरमीत","Gurmeet"),("सुखविंदर","Sukhwinder"),("बलजीत","Baljeet"),("रजनी","Rajni"),("शकुंतला","Shakuntala"),
 ("विमला","Vimla"),("सरोज","Saroj"),("शीला","Sheela")]
SURNAME = [("शर्मा","Sharma"),("वर्मा","Verma"),("गुप्ता","Gupta"),("कुमार","Kumar"),("यादव","Yadav"),
 ("चौहान","Chauhan"),("मिश्रा","Mishra"),("पांडे","Pandey"),("तिवारी","Tiwari"),("सैनी","Saini"),
 ("मल्होत्रा","Malhotra"),("कपूर","Kapoor"),("अरोड़ा","Arora"),("भाटिया","Bhatia"),("गिल","Gill"),
 ("संधू","Sandhu"),("ढिल्लों","Dhillon"),("ग्रेवाल","Grewal"),("सिद्धू","Sidhu"),("बराड़","Brar"),
 ("सिंह","Singh"),("चौधरी","Chaudhary"),("मेहरा","Mehra"),("खन्ना","Khanna"),("वालिया","Walia"),
 ("जोशी","Joshi"),("राणा","Rana"),("बेदी","Bedi")]
# Latin spelling variants (realistic transliteration noise): pattern -> replacement
LAT_OPS = [("ee","i"),("i","ee"),("oo","u"),("u","oo"),("sh","s"),("v","w"),("w","v"),("aa","a"),("kh","k"),("ph","f")]
# Devanagari spelling variants
DEV_OPS = [("र्म","रम"),("ी","ि"),("ि","ी"),("ू","ु"),("ु","ू"),("श","स"),("ं","न्"),("ड़","ड")]
