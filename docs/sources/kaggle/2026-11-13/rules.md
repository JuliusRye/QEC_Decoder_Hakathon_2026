# Kaggle Rules — captured November 13, 2026

Source: https://www.kaggle.com/competitions/quantum-error-correction-decoder/rules

Capture: signed-in Firefox Save Page, approximately 06:10 EST (11:10 UTC), then Defuddle Markdown extraction. The competition-specific rules and all 18 foundational sections follow. Browser navigation, account acceptance status, and page-footer text were removed; operative rule wording is preserved. This is a dated source copy, not confirmation that the live page has remained unchanged. Do not edit the source wording to resolve conflicts; record interpretation in `docs/COMPETITION.md`.

---

## Competition Rules

## Competition Rules

### The short version

- **Write your own decoder.** Existing decoder packages and pretrained decoders are not allowed.
- **Generate as much extra data as you like** from the provided circuits.
- **Your predictions must come from your decoder.** No hand-labelling, and no tuning individual predictions against the leaderboard.
- **The top 10 teams hand in their code.** We check it for banned libraries and re-run it on our timing machine (one NVIDIA B200 GPU with 48 CPU cores) to time it. Their final ranking combines LER and runtime (see the Evaluation section of the Overview). **If the handed-in code doesn't reproduce the team's submission on the leaderboard, the team is disqualified.**

### 1\. Write your own decoder

Your decoder must be your own work. You may **not** use existing implementations of QEC decoders, or code copied from them. This includes:

- `pymatching`, `ldpc`, `stimbposd`, `beliefmatching`, `tesseract-decoder` and `fusion-blossom`
- any other package or code whose purpose is decoding quantum error-correcting codes
- pretrained decoder models made by others

You may use general-purpose libraries, for example `numpy`, `scipy`, `numba`, `pytorch`, `jax`, `scikit-learn`, graph libraries and general optimisation solvers (LP, ILP, SAT). You may use Stim to load the circuits, sample data and build detector error models. You may train your own models, such as neural networks, on data you generate.

If you are unsure whether a library is allowed, ask in the Discussion forum before you rely on it.

### 2\. Data

- The competition data are released under the MIT license.
- Generating more data is allowed and encouraged. Use Stim to sample as many shots as you like from `X_circuit.stim` and `Z_circuit.stim`, or from circuits you build yourself (for example with other noise strengths) for training.
- Your predictions must be produced by running your decoder on the detector events in `test.csv`. Labelling test shots by hand, editing predictions by hand, and using leaderboard feedback to tune individual predictions are not allowed.

### 3\. Submissions

- Use the format of `sample_submission.csv`: the columns `id, L0, L1, L2, L3` **in that order**, one row per test shot, with every prediction 0 or 1.
- The score is the mean absolute error (MAE) over all predictions, which equals the logical error rate (LER). Lower is better.
- The Public leaderboard is calculated on about 30% of the test shots. The final ranking uses the other 70% (the Private leaderboard).
- Each team may make at most 10 submissions in total.
- You may select up to 2 final submissions. The better Private score of the two counts.

### 4\. Participants and teams

- **Students only.** This is a student hackathon: every team member must be a student enrolled at a university and 18 or older at the time of entry. Members of the Novo Nordisk Foundation Quantum Computing Programme (NQCP) may take part if they are students, but can't receive the prize (see section 7). We may ask for proof of enrolment.
- This is an invite-only competition. Teams may have up to 4 members. Each person may use only one Kaggle account.
- Sharing code or predictions privately between teams is not allowed. Sharing code with all participants, in this competition's Discussion or Code tabs, is allowed, as long as the shared code follows these rules.

### 5\. Code check for the top 10

After the competition closes, the top 10 teams on the Private leaderboard must hand in the code behind their selected submission by **14 November 2026 at 07:00 CET** (06:00 UTC). We check it for banned libraries, re-run it and time it.

Hand in a folder containing:

- `decoder.py`, which defines this function:
```python
def decode(circuit: stim.Circuit, detector_events: np.ndarray) -> np.ndarray:
    """
    circuit: the X or Z circuit, loaded with stim.Circuit.from_file.
    detector_events: bool array of shape (shots, 70), columns D0 to D69.
    Returns a 0/1 array of shape (shots, 4), columns L0 to L3.
    """
```
- `requirements.txt`, listing every package you use, pinned to an exact version (for example `numpy==2.2.6`).
- Any files `decode` loads, such as trained weights or lookup tables, together with the code that created them.

**Your folder must run the way we run it.** We run every hand-in the same way we run our own reference decoders on the timing machine. We copy your folder there, create a fresh virtual environment (Linux, Python \[3.13\]), install your packages with `pip install -r requirements.txt`, and then import `decode` from `decoder.py`. Nothing else is installed, and `decode` runs without internet access. Test this before you hand in; the Overview's *Handing in your code* section shows how.

We call `decode` once per basis on that basis's 100,000 test shots, without internet access, on our timing machine (see **Hardware** below). The runtime t is the total wall-clock time of the two calls, taking the median of 5 runs. Only these two calls are timed: importing `decoder.py`, and anything it builds or loads when it is imported, happens before the clock starts.

**Your code must reproduce your submission.** The predictions your handed-in code makes on the test shots must match the selected submission that is scored on the leaderboard, for every shot. If they don't, your team is disqualified. If your decoder uses randomness, fix its seed, and make sure any GPU code gives the same result on every run.

**Hardware.** We time every decoder, and our own reference decoder that sets t\_cap, on the same machine on UCloud (DeiC Interactive HPC, SDU/K8s):

| Machine type | GPU | CPU | Memory |
| --- | --- | --- | --- |
| `gpu-nvidia-b200-1-gpu` | 1 NVIDIA B200 | 48 vCPUs, AMD EPYC 9655 | 288 GB |

- **You don't need this hardware yourself.** Write your decoder for whatever you have: a laptop, a single CPU core, or a GPU are all fine. The timing machine is the most your decoder can use, not what it must use. It may use the GPU, the CPU cores, or both, but it doesn't have to. Its runtime is measured on this machine either way, so a decoder that uses more of it can run faster.
- Multi-threading is allowed. We set `OMP_NUM_THREADS` and `NUMBA_NUM_THREADS` to 48.
- We'll publish the exact software environment (the Python and CUDA versions) with the hand-in instructions.
- Time spent waiting in the queue for the machine doesn't count towards your runtime.

A team is disqualified, which removes it from the final ranking and moves the teams below it up, if it:

- doesn't hand in its code on time,
- hands in code that doesn't install and run as described above,
- uses a banned library or banned code,
- hands in code whose predictions don't match its selected submission on the leaderboard, or
- has a runtime t longer than the hard limit t\_max = 5 minutes.

By handing in code, you allow the organisers to inspect, run and time it to verify your result.

### 6\. Final ranking

The top 10 teams that pass the code check are ranked by their final score:

- **Formula:** final score = Private LER × max(1, t / t\_cap)^α, where lower is better, t\_cap = 0.56 s is the runtime of our reference decoder on the same machine, and α = 0.07.
- **What it means:** a decoder within t\_cap keeps its LER unchanged, and each doubling of the runtime beyond t\_cap multiplies the score by 2^α = 1.05.
- **Ties** in the final score are broken by the shorter runtime.
- **All other teams** are ranked by their Private LER.

See the Evaluation section of the Overview for details.

**Presentations.** The top 3 teams in the final ranking each submit a 5-minute video explaining their solution, by email by **16 November 2026 at 07:00 CET**. Judges from Riverlane and NVIDIA pick the winning team from these videos, and it receives the prize in section 7.

### 7\. Prize

The winning team wins a trip to Copenhagen to visit the Novo Nordisk Foundation Quantum Computing Programme (NQCP) at the Niels Bohr Institute, University of Copenhagen.

- **What's covered:** for every member of the winning team (up to 4 people), return economy travel to Copenhagen, 3 nights' accommodation and local transport during the visit. The organisers choose the accommodation. Everything else, including passports, visas, insurance and personal expenses, is at the winners' own cost.
- **When:** the trip must be arranged and booked within **2 months of the announcement of the final results**. If it isn't booked by then, the prize lapses.
- **Agree before you book:** before ordering tickets or anything else for the trip, the winners must agree the dates and the budget with the organisers. Only costs that the organisers approved in writing (for example by email) before booking are covered.
- **Travel documents and visas:** Winners are responsible for holding valid travel documents. Winners are responsible for obtaining any required visa or entry authorization for Denmark — the organizers will provide an official invitation letter to support visa applications, but cannot guarantee issuance. Visa processing can take several weeks, so start straight away. If a winner can't get the documents they need in time, the prize lapses for that person.
- **Eligibility:** every team member must be a student and 18 or older at the time of entry (see section 4). Members of NQCP may take part if they are students, but can't receive the prize themselves. The prize won't be awarded where this would break applicable law, including EU, UN or Danish sanctions, or the University of Copenhagen's policies, including its rules for visitors. In that case the organisers may adapt the visit, replace it or withhold the prize.
- **No alternatives:** the prize can't be exchanged for cash or transferred.
- **Changes:** if travel isn't possible for reasons outside the organisers' control, they may postpone the trip, replace it with a virtual visit, or cancel it.
- **Your responsibilities:** you are responsible for any tax on the prize, and for checking that your employer or school allows you to accept it. You travel at your own risk and must have travel and health insurance. To the extent the law allows, the organisers aren't liable for delays, cancellations, injury or loss.
- **Personal data:** details needed to book the trip are used only for that purpose, under the University of Copenhagen's privacy policy.
- **Awarding:** the prize goes to the team picked from the top-3 presentations (section 6), and only after it has passed the code check (section 5).
- The prize is provided by the organisers, not by Kaggle.

### 8\. Timeline

All times are CET (Copenhagen). Kaggle shows its deadlines in UTC, which is one hour earlier. The Zoom links are in the confirmation email.

- Team registration closes: **11 November 2026 at 12:00 CET**
- Opening remarks (Zoom): **13 November 2026, 11:45–11:55 CET**
- Start: **13 November 2026 at 12:00 CET** (11:00 UTC)
- Online technical support (Zoom): **13 November 2026, 12:00–13:00 and 16:00–17:00 CET**
- Final submission deadline: **13 November 2026 at 24:00 CET**, midnight (23:00 UTC)
- Code hand-in for the top 10: right after the deadline, by **14 November 2026 at 07:00 CET** (06:00 UTC)
- Top 3 announced, with closing remarks (Zoom): **14 November 2026, 12:45–13:00 CET**
- 5-minute videos from the top 3 (by email): **16 November 2026 at 07:00 CET**
- Winner chosen (final results): **16 November 2026 at 11:00 CET**
- Prize trip booked by: **16 January 2027** (2 months after the final results)

### Questions

Ask in the Discussion forum. If you are unsure whether something is allowed, ask before you rely on it.

## Kaggle Competition Foundational Rules

(Non-editable)

warning

Competition participants must also agree to Kaggle's Foundational Competition Rules. These rules will supersede the competition-specific rules in the event of any conflict.

The following Kaggle Competition Foundational Rules (“ Foundational Rules ”) apply to every competition regardless of whether the Sponsor creates competition-specific rules. Any competition-specific rules provided by the Sponsor are in addition to these rules, and in the case of any conflict or inconsistency, these Foundational Rules control and nullify contrary competition-specific rules.

### GENERAL COMPETITION RULES - BINDING AGREEMENT

#### 1\. ELIGIBILITY

a. To be eligible to enter the Competition, you must be:

1. a registered account holder at Kaggle.com;
2. the older of 18 years old or the age of majority in your jurisdiction of residence (unless otherwise agreed to by Competition Sponsor and appropriate parental/guardian consents have been obtained by Competition Sponsor);
3. not a resident of Crimea, so-called Donetsk People's Republic (DNR) or Luhansk People's Republic (LNR), Cuba, Iran, or North Korea; and
4. not a person or representative of an entity under U.S. export controls or sanctions (see: [https://www.treasury.gov/resourcecenter/sanctions/Programs/Pages/Programs.aspx](https://www.treasury.gov/resource-center/sanctions/Programs/Pages/Programs.aspx)).

b. Competitions are open to residents of the United States and worldwide, except that if you are a resident of Crimea, so-called Donetsk People's Republic (DNR) or Luhansk People's Republic (LNR), Cuba, Iran, North Korea, or are subject to U.S. export controls or sanctions, you may not enter the Competition. Other local rules and regulations may apply to you, so please check your local laws to ensure that you are eligible to participate in skills-based competitions. The Competition Host reserves the right to forego or award alternative Prizes where needed to comply with local laws. If a winner is located in a country where prizes cannot be awarded, then they are not eligible to receive a prize.

c. If you are entering as a representative of a company, educational institution or other legal entity, or on behalf of your employer, these rules are binding on you, individually, and the entity you represent or where you are an employee. If you are acting within the scope of your employment, or as an agent of another party, you warrant that such party or your employer has full knowledge of your actions and has consented thereto, including your potential receipt of a Prize. You further warrant that your actions do not violate your employer's or entity's policies and procedures.

d. The Competition Sponsor reserves the right to verify eligibility and to adjudicate on any dispute at any time. If you provide any false information relating to the Competition concerning your identity, residency, mailing address, telephone number, email address, ownership of right, or information required for entering the Competition, you may be immediately disqualified from the Competition.

#### 2\. SPONSOR AND HOSTING PLATFORM

a. The Competition is sponsored by Competition Sponsor named above. The Competition is hosted on behalf of Competition Sponsor by Kaggle Inc. ("Kaggle"). Kaggle is an independent contractor of Competition Sponsor, and is not a party to this or any agreement between you and Competition Sponsor. You understand that Kaggle has no responsibility with respect to selecting the potential Competition winner(s) or awarding any Prizes. Kaggle will perform certain administrative functions relating to hosting the Competition, and you agree to abide by the provisions relating to Kaggle under these Rules. As a Kaggle.com account holder and user of the Kaggle competition platform, remember you have accepted and are subject to the Kaggle Terms of Service at [www.kaggle.com/terms](http://www.kaggle.com/terms) in addition to these Rules.

#### 3\. COMPETITION PERIOD

a. For the purposes of Prizes, the Competition will run from the Start Date and time to the Final Submission Deadline (such duration the “Competition Period”). The Competition Timeline is subject to change, and Competition Sponsor may introduce additional hurdle deadlines during the Competition Period. Any updated or additional deadlines will be publicized on the Competition Website. It is your responsibility to check the Competition Website regularly to stay informed of any deadline changes. YOU ARE RESPONSIBLE FOR DETERMINING THE CORRESPONDING TIME ZONE IN YOUR LOCATION.

#### 4\. COMPETITION ENTRY

a. NO PURCHASE NECESSARY TO ENTER OR WIN. To enter the Competition, you must register on the Competition Website prior to the Entry Deadline, and follow the instructions for developing and entering your Submission through the Competition Website. Your Submissions must be made in the manner and format, and in compliance with all other requirements, stated on the Competition Website (the "Requirements"). Submissions must be received before any Submission deadlines stated on the Competition Website. Submissions not received by the stated deadlines will not be eligible to receive a Prize. b. Submissions may not use or incorporate information from hand labeling or human prediction of the validation dataset or test data records. c. If the Competition is a multi-stage competition with temporally separate training and/or test data, one or more valid Submissions may be required during each Competition stage in the manner described on the Competition Website in order for the Submissions to be Prize eligible. d. Submissions are void if they are in whole or part illegible, incomplete, damaged, altered, counterfeit, obtained through fraud, or late. Competition Sponsor reserves the right to disqualify any entrant who does not follow these Rules, including making a Submission that does not meet the Requirements.

#### 5\. INDIVIDUALS AND TEAMS

a. Individual Account. You may make Submissions only under one, unique Kaggle.com account. You will be disqualified if you make Submissions through more than one Kaggle account, or attempt to falsify an account to act as your proxy. You may submit up to the maximum number of Submissions per day as specified on the Competition Website. b. Teams. If permitted under the Competition Website guidelines, multiple individuals may collaborate as a Team; however, you may join or form only one Team. Each Team member must be a single individual with a separate Kaggle account. You must register individually for the Competition before joining a Team. You must confirm your Team membership to make it official by responding to the Team notification message sent to your Kaggle account. Team membership may not exceed the Maximum Team Size stated on the Competition Website. c. Team Merger. Teams may request to merge via the Competition Website. Team mergers may be allowed provided that: (i) the combined Team does not exceed the Maximum Team Size; (ii) the number of Submissions made by the merging Teams does not exceed the number of Submissions permissible for one Team at the date of the merger request; (iii) the merger is completed before the earlier of: any merger deadline or the Competition deadline; and (iv) the proposed combined Team otherwise meets all the requirements of these Rules. d. Private Sharing. No private sharing outside of Teams. Privately sharing code or data outside of Teams is not permitted. It's okay to share code if made available to all Participants on the forums.

#### 6\. SUBMISSION CODE REQUIREMENTS

a. Private Code Sharing. Unless otherwise specifically permitted under the Competition Website or Competition Specific Rules above, during the Competition Period, you are not allowed to privately share source or executable code developed in connection with or based upon the Competition Data or other source or executable code relevant to the Competition (“Competition Code”). This prohibition includes sharing Competition Code between separate Teams, unless a Team merger occurs. Any such sharing of Competition Code is a breach of these Competition Rules and may result in disqualification. b. Public Code Sharing. You are permitted to publicly share Competition Code, provided that such public sharing does not violate the intellectual property rights of any third party. If you do choose to share Competition Code or other such code, you are required to share it on Kaggle.com on the discussion forum or notebooks associated specifically with the Competition for the benefit of all competitors. By so sharing, you are deemed to have licensed the shared code under an Open Source Initiative-approved license (see [www.opensource.org](http://www.opensource.org/)) that in no event limits commercial use of such Competition Code or model containing or depending on such Competition Code. c. Use of Open Source. Unless otherwise stated in the Specific Competition Rules above, if open source code is used in the model to generate the Submission, then you must only use open source code licensed under an Open Source Initiative-approved license (see [www.opensource.org](http://www.opensource.org/)) that in no event limits commercial use of such code or model containing or depending on such code.

#### 7\. DETERMINING WINNERS

a. Each Submission will be scored and ranked by the evaluation metric stated on the Competition Website. During the Competition Period, the current ranking will be visible on the Competition Website's Public Leaderboard. The potential winner(s) are determined solely by the leaderboard ranking on the Private Leaderboard, subject to compliance with these Rules. The Public Leaderboard will be based on the public test set and the Private Leaderboard will be based on the private test set. b. In the event of a tie, the Submission that was entered first to the Competition will be the winner. In the event a potential winner is disqualified for any reason, the Submission that received the next highest score rank will be chosen as the potential winner.

#### 8\. NOTIFICATION OF WINNERS & DISQUALIFICATION

a. The potential winner(s) will be notified by email. b. If a potential winner (i) does not respond to the notification attempt within one (1) week from the first notification attempt or (ii) notifies Kaggle within one week after the Final Submission Deadline that the potential winner does not want to be nominated as a winner or does not want to receive a Prize, then, in each case (i) and (ii) such potential winner will not receive any Prize, and an alternate potential winner will be selected from among all eligible entries received based on the Competition’s judging criteria. c. In case (i) and (ii) above Kaggle may disqualify the Participant. However, in case (ii) above, if requested by Kaggle, such potential winner may provide code and documentation to verify the Participant’s compliance with these Rules. If the potential winner provides code and documentation to the satisfaction of Kaggle, the Participant will not be disqualified pursuant to this paragraph. d. Competition Sponsor reserves the right to disqualify any Participant from the Competition if the Competition Sponsor reasonably believes that the Participant has attempted to undermine the legitimate operation of the Competition by cheating, deception, or other unfair playing practices or abuses, threatens or harasses any other Participants, Competition Sponsor or Kaggle. e. A disqualified Participant may be removed from the Competition leaderboard, at Kaggle's sole discretion. If a Participant is removed from the Competition Leaderboard, additional winning features associated with the Kaggle competition platform, for example Kaggle points or medals, may also not be awarded. f. The final leaderboard list will be publicly displayed at Kaggle.com. Determinations of Competition Sponsor are final and binding.

#### 9\. PRIZES

a. Prize(s) are as described on the Competition Website and are only available for winning during the time period described on the Competition Website. The odds of winning any Prize depends on the number of eligible Submissions received during the Competition Period and the skill of the Participants. b. All Prizes are subject to Competition Sponsor's review and verification of the Participant’s eligibility and compliance with these Rules, and the compliance of the winning Submissions with the Submissions Requirements. In the event that the Submission demonstrates non-compliance with these Competition Rules, Competition Sponsor may at its discretion take either of the following actions: (i) disqualify the Submission(s); or (ii) require the potential winner to remediate within one week after notice all issues identified in the Submission(s) (including, without limitation, the resolution of license conflicts, the fulfillment of all obligations required by software licenses, and the removal of any software that violates the software restrictions). c. A potential winner may decline to be nominated as a Competition winner in accordance with Section 3.8. d. Potential winners must return all required Prize acceptance documents within two (2) weeks following notification of such required documents, or such potential winner will be deemed to have forfeited the prize and another potential winner will be selected. Prize(s) will be awarded within approximately thirty (30) days after receipt by Competition Sponsor or Kaggle of the required Prize acceptance documents. Transfer or assignment of a Prize is not allowed. e. You are not eligible to receive any Prize if you do not meet the Eligibility requirements in Section 2.7 and Section 3.1 above. f. If a Team wins a monetary Prize, the Prize money will be allocated in even shares between the eligible Team members, unless the Team unanimously opts for a different Prize split and notifies Kaggle before Prizes are issued.

#### 10\. TAXES

a. ALL TAXES IMPOSED ON PRIZES ARE THE SOLE RESPONSIBILITY OF THE WINNERS. Payments to potential winners are subject to the express requirement that they submit all documentation requested by Competition Sponsor or Kaggle for compliance with applicable state, federal, local and foreign (including provincial) tax reporting and withholding requirements. Prizes will be net of any taxes that Competition Sponsor is required by law to withhold. If a potential winner fails to provide any required documentation or comply with applicable laws, the Prize may be forfeited and Competition Sponsor may select an alternative potential winner. Any winners who are U.S. residents will receive an IRS Form-1099 in the amount of their Prize.

#### 11\. GENERAL CONDITIONS

a. All federal, state, provincial and local laws and regulations apply.

#### 12\. PUBLICITY

a. You agree that Competition Sponsor, Kaggle and its affiliates may use your name and likeness for advertising and promotional purposes without additional compensation, unless prohibited by law.

#### 13\. PRIVACY

a. You acknowledge and agree that Competition Sponsor and Kaggle may collect, store, share and otherwise use personally identifiable information provided by you during the Kaggle account registration process and the Competition, including but not limited to, name, mailing address, phone number, and email address (“Personal Information”). Kaggle acts as an independent controller with regard to its collection, storage, sharing, and other use of this Personal Information, and will use this Personal Information in accordance with its Privacy Policy < [www.kaggle.com/privacy](http://www.kaggle.com/privacy) >, including for administering the Competition. As a Kaggle.com account holder, you have the right to request access to, review, rectification, portability or deletion of any personal data held by Kaggle about you by logging into your account and/or contacting Kaggle Support at < [www.kaggle.com/contact](http://www.kaggle.com/contact) >. b. As part of Competition Sponsor performing this contract between you and the Competition Sponsor, Kaggle will transfer your Personal Information to Competition Sponsor, which acts as an independent controller with regard to this Personal Information. As a controller of such Personal Information, Competition Sponsor agrees to comply with all U.S. and foreign data protection obligations with regard to your Personal Information. Kaggle will transfer your Personal Information to Competition Sponsor in the country specified in the Competition Sponsor Address listed above, which may be a country outside the country of your residence. Such country may not have privacy laws and regulations similar to those of the country of your residence.

#### 14\. WARRANTY, INDEMNITY AND RELEASE

a. You warrant that your Submission is your own original work and, as such, you are the sole and exclusive owner and rights holder of the Submission, and you have the right to make the Submission and grant all required licenses. You agree not to make any Submission that: (i) infringes any third party proprietary rights, intellectual property rights, industrial property rights, personal or moral rights or any other rights, including without limitation, copyright, trademark, patent, trade secret, privacy, publicity or confidentiality obligations, or defames any person; or (ii) otherwise violates any applicable U.S. or foreign state or federal law. b. To the maximum extent permitted by law, you indemnify and agree to keep indemnified Competition Entities at all times from and against any liability, claims, demands, losses, damages, costs and expenses resulting from any of your acts, defaults or omissions and/or a breach of any warranty set forth herein. To the maximum extent permitted by law, you agree to defend, indemnify and hold harmless the Competition Entities from and against any and all claims, actions, suits or proceedings, as well as any and all losses, liabilities, damages, costs and expenses (including reasonable attorneys fees) arising out of or accruing from: (a) your Submission or other material uploaded or otherwise provided by you that infringes any third party proprietary rights, intellectual property rights, industrial property rights, personal or moral rights or any other rights, including without limitation, copyright, trademark, patent, trade secret, privacy, publicity or confidentiality obligations, or defames any person; (b) any misrepresentation made by you in connection with the Competition; (c) any non-compliance by you with these Rules or any applicable U.S. or foreign state or federal law; (d) claims brought by persons or entities other than the parties to these Rules arising from or related to your involvement with the Competition; and (e) your acceptance, possession, misuse or use of any Prize, or your participation in the Competition and any Competition-related activity. c. You hereby release Competition Entities from any liability associated with: (a) any malfunction or other problem with the Competition Website; (b) any error in the collection, processing, or retention of any Submission; or (c) any typographical or other error in the printing, offering or announcement of any Prize or winners.

#### 15\. INTERNET

a. Competition Entities are not responsible for any malfunction of the Competition Website or any late, lost, damaged, misdirected, incomplete, illegible, undeliverable, or destroyed Submissions or entry materials due to system errors, failed, incomplete or garbled computer or other telecommunication transmission malfunctions, hardware or software failures of any kind, lost or unavailable network connections, typographical or system/human errors and failures, technical malfunction(s) of any telephone network or lines, cable connections, satellite transmissions, servers or providers, or computer equipment, traffic congestion on the Internet or at the Competition Website, or any combination thereof, which may limit a Participant’s ability to participate.

#### 16\. RIGHT TO CANCEL, MODIFY OR DISQUALIFY

a. If for any reason the Competition is not capable of running as planned, including infection by computer virus, bugs, tampering, unauthorized intervention, fraud, technical failures, or any other causes which corrupt or affect the administration, security, fairness, integrity, or proper conduct of the Competition, Competition Sponsor reserves the right to cancel, terminate, modify or suspend the Competition. Competition Sponsor further reserves the right to disqualify any Participant who tampers with the submission process or any other part of the Competition or Competition Website. Any attempt by a Participant to deliberately damage any website, including the Competition Website, or undermine the legitimate operation of the Competition is a violation of criminal and civil laws. Should such an attempt be made, Competition Sponsor and Kaggle each reserves the right to seek damages from any such Participant to the fullest extent of the applicable law.

#### 17\. NOT AN OFFER OR CONTRACT OF EMPLOYMENT

a. Under no circumstances will the entry of a Submission, the awarding of a Prize, or anything in these Rules be construed as an offer or contract of employment with Competition Sponsor or any of the Competition Entities. You acknowledge that you have submitted your Submission voluntarily and not in confidence or in trust. You acknowledge that no confidential, fiduciary, agency, employment or other similar relationship is created between you and Competition Sponsor or any of the Competition Entities by your acceptance of these Rules or your entry of your Submission.

#### 18\. DEFINITIONS

a. "Competition Data" are the data or datasets available from the Competition Website for the purpose of use in the Competition, including any prototype or executable code provided on the Competition Website. The Competition Data will contain private and public test sets. Which data belongs to which set will not be made available to Participants. b. An “Entry” is when a Participant has joined, signed up, or accepted the rules of a competition. Entry is required to make a Submission to a competition. c. A “Final Submission” is the Submission selected by the user, or automatically selected by Kaggle in the event not selected by the user, that is/are used for final placement on the competition leaderboard. d. A “Participant” or “Participant User” is an individual who participates in a competition by entering the competition and making a Submission. e. The “Private Leaderboard” is a ranked display of Participants’ Submission scores against the private test set. The Private Leaderboard determines the final standing in the competition. f. The “Public Leaderboard” is a ranked display of Participants’ Submission scores against a representative sample of the test data. This leaderboard is visible throughout the competition. g. A “Sponsor” is responsible for hosting the competition, which includes but is not limited to providing the data for the competition, determining winners, and enforcing competition rules. h. A “Submission” is anything provided by the Participant to the Sponsor to be evaluated for competition purposes and determine leaderboard position. A Submission may be made as a model, notebook, prediction file, or other format as determined by the Sponsor. i. A “Team” is one or more Participants participating together in a Kaggle competition, by officially merging together as a Team within the competition platform.
