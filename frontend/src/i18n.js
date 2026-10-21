import React, { createContext, useContext, useState } from "react";

export const dictionary = {
  en: {
    // Brand / Common
    brand_tagline: "Karuthal · Care Before Crisis",
    brand_name: "KARUTHAL",
    care_before_crisis: "Care Before Crisis",
    back: "← Back",
    proto_footer: "Demo prototype. Test data only.",
    report_concern: "Report a concern",
    emergency_help: "Emergency help",
    officer_login: "Officer login",
    officer_sign_in: "Officer sign in",

    // Notices
    report_notice: "Demo prototype: nothing here is sent to real authorities. Use test data only.",
    emergency_notice: "Demo prototype: this call is simulated and does not reach a real helpline. In a real emergency use your phone dialer.",
    report_legal_footer: "A report is a concern for trained staff to assess. It is not proof, and nobody is named as guilty.",

    // Report Form
    report_title: "Report a Concern",
    report_subtitle: "Write what you saw. We do not ask for your name or phone number.",
    type_of_concern: "Type of concern",
    select_concern_type: "-- Select concern category --",
    what_did_you_see: "What did you see?",
    what_did_you_see_helper: "Describe only what you saw or heard. You do not need to guess who is at fault.",
    what_did_you_see_placeholder: "Provide specific details of what you observed, hearing sounds, clothing or appearance, surroundings, etc.",
    voice_box_title: "Voice input",
    voice_lang: "Voice language",
    voice_speak: "Speak instead of typing",
    voice_listening: "Listening... Speak now",
    voice_stop: "Stop voice input",
    voice_helper: "Voice-to-text is not perfect. Please check and edit the text before you submit.",
    voice_unsupported: "Voice recognition is not supported in this browser. Please type your observations.",
    where_did_you_see: "Where did you see it?",
    where_helper: "Place name or nearby landmark (max 200 chars)",
    where_placeholder: "e.g., Near railway station, behind bus stand, market junction",
    district: "District",
    select_district: "-- Select District --",
    approx_time: "Approximate time",
    approx_time_placeholder: "For example: around 5:30 PM",
    photo_title: "Photo of the person (optional)",
    photo_helper: "Only add a photo if you already have one or can take it safely from a distance. Never approach, follow or confront anyone to get a photo.",
    photo_warning: "Do not photograph a child.",
    photo_take: "Take photo",
    photo_choose: "Choose from gallery",
    photo_remove: "Remove photo",
    photo_confirm_no_child: "I confirm this photo does not show a child.",
    photo_not_uploaded_notice: "Photos are not uploaded in this demo.",
    immediate_danger_title: "Is the child in immediate danger?",
    immediate_danger_yes: "Yes",
    immediate_danger_no: "No",
    immediate_danger_not_sure: "Not sure",
    share_location: "Share my approximate area (about 1 km) with the district child protection officer.",
    location_locating: "Requesting location...",
    location_active: "Approximate location attached (~1 km precision).",
    location_denied: "Location access was not granted. Report will be submitted without coordinates.",
    location_out_of_bounds: "Location is outside Kerala boundaries and will not be shared.",
    submit_report: "Submit report",
    submitting: "Submitting...",

    // Confirmation Screen
    report_success_title: "Report Submitted",
    report_success_subtitle: "Your concern has been securely logged for review by the district officer.",
    case_ref_label: "Report ID",
    reporter_token_label: "One-time Callback Token",
    reporter_token_warning: "Save this now. It cannot be shown again.",
    copy_token: "Copy Token",
    token_copied: "Copied to clipboard!",
    callback_title: "Request a Callback",
    callback_desc: "If you wish to allow an officer to contact you securely without revealing your identity:",
    callback_btn: "Request a callback",
    callback_requested: "Callback requested. An officer may initiate a secure call through this portal.",
    callback_already_requested: "Callback already requested for this report.",
    submit_another: "Submit another concern",

    // Emergency Screen
    emergency_title: "Emergency help",
    emergency_subtitle: "Tap once to call the nearest women helpline. No dialing needed.",
    start_call: "Start call",
    connecting: "Connecting...",
    emergency_privacy_note: "Your location is used only to find the closest helpline. We never ask for your name or phone number.",
    use_phone_dialer: "Use phone dialer instead",
    opens_phone_dialer: "Opens your phone dialer",
    women_helpline: "Women Helpline",
    connecting_message: "Connecting you to the nearest helpline...",
    connected_demo: "Connected (demo)",
    connected_tip: "Tell them where you are and what is happening.",
    end_call: "End call",
    call_ended: "Call ended",
    call_duration: "Duration",
    write_report_now: "Write a report now",
    back_to_home: "Back to home",
    emergency_district_label: "Nearest District Helpline",

    // Officer Login Screen
    officer_signin_title: "Officer sign in",
    officer_signin_subtitle: "For police and child-protection personnel who review reports. Reporters don't need an account.",
    officer_id_or_email: "Officer ID or official email",
    officer_id_placeholder: "e.g., DCPU-TVM-01 or officer@kerala.gov.in",
    password: "Password",
    show_password: "Show",
    hide_password: "Hide",
    forgot_password: "Forgot password?",
    forgot_password_message: "Officer accounts are issued by your department. Contact your administrator.",
    sign_in: "Sign in",
    signing_in: "Signing in...",
    officer_notice_line: "Officer accounts are issued by your department. Contact your administrator for access.",
    no_signin_needed_divider: "Reporting a concern? No sign-in needed",

    // Categories
    cat_physical: "Physical abuse",
    cat_sexual: "Sexual abuse",
    cat_emotional: "Emotional abuse",
    cat_neglect: "Neglect",
    cat_labour: "Child labour",
    cat_marriage: "Child marriage",
    cat_trafficking: "Trafficking",
    cat_missing: "Missing child",
    cat_other: "Other",
  },
  ml: {
    // Brand / Common
    brand_tagline: "കരുതൽ · പ്രതിസന്ധിക്ക് മുൻപ് കരുതൽ",
    brand_name: "കരുതൽ (KARUTHAL)",
    care_before_crisis: "പ്രതിസന്ധിക്ക് മുൻപ് കരുതൽ",
    back: "← തിരികെ",
    proto_footer: "ഡെമോ പ്രോട്ടോടൈപ്പ്. പരീക്ഷണ വിവരങ്ങൾ മാത്രം.",
    report_concern: "ആശങ്ക അറിയിക്കുക",
    emergency_help: "അടിയന്തിര സഹായം",
    officer_login: "ഓഫീസർ ലോഗിൻ",
    officer_sign_in: "ഓഫീസർ സൈൻ ഇൻ",

    // Notices
    report_notice: "ഡെമോ പ്രോട്ടോടൈപ്പ്: ഇവിടെ നൽകുന്ന വിവരങ്ങൾ യഥാർത്ഥ അധികാരികൾക്ക് അയക്കില്ല. പരീക്ഷണ വിവരങ്ങൾ മാത്രം ഉപയോഗിക്കുക.",
    emergency_notice: "ഡെമോ പ്രോട്ടോടൈപ്പ്: ഈ കോൾ ഒരു സിമുലേഷനാണ്, യഥാർത്ഥ ഹെൽപ്‌ലൈനിൽ എത്തില്ല. യഥാർത്ഥ അടിയന്തിര സാഹചര്യത്തിൽ ഫോൺ ഡയലർ ഉപയോഗിക്കുക.",
    report_legal_footer: "നൽകിയ വിവരം പരിശീലനം ലഭിച്ച ഉദ്യോഗസ്ഥർ പരിശോധിക്കുന്നതിനുള്ളതാണ്. ഇത് തെളിവല്ല, ആരെയും കുറ്റക്കാരായി കാണുന്നില്ല.",

    // Report Form
    report_title: "ആശങ്ക അറിയിക്കുക",
    report_subtitle: "നിങ്ങൾ കണ്ടത് എഴുതുക. നിങ്ങളുടെ പേരോ ഫോൺ നമ്പറോ ഞങ്ങൾ ചോദിക്കുന്നില്ല.",
    type_of_concern: "ആശങ്കയുടെ തരം",
    select_concern_type: "-- വിഭാഗം തിരഞ്ഞെടുക്കുക --",
    what_did_you_see: "നിങ്ങൾ എന്താണ് കണ്ടത്?",
    what_did_you_see_helper: "നിങ്ങൾ കണ്ടതോ കേട്ടതോ മാത്രം വിവരിക്കുക. ആരുടെ തെറ്റാണെന്ന് ഊഹിക്കേണ്ടതില്ല.",
    what_did_you_see_placeholder: "നിങ്ങൾ കണ്ട കാര്യങ്ങൾ, ശബ്ദങ്ങൾ, വസ്ത്രധാരണം, ചുറ്റുപാടുകൾ തുടങ്ങിയവ വ്യക്തമായി എഴുതുക.",
    voice_box_title: "ശബ്ദ ഇൻപുട്ട്",
    voice_lang: "ശബ്ദ ഭാഷ",
    voice_speak: "ടൈപ്പ് ചെയ്യുന്നതിന് പകരം സംസാരിക്കുക",
    voice_listening: "കേൾക്കുന്നു... സംസാരിക്കുക",
    voice_stop: "ശബ്ദ ഇൻപുട്ട് നിർത്തുക",
    voice_helper: "വോയ്‌സ്-ടു-ടെക്‌സ്റ്റ് പൂർണ്ണമല്ല. സമർപ്പിക്കുന്നതിന് മുൻപ് ദയവായി പരിശോധിച്ച് തിരുത്തുക.",
    voice_unsupported: "ഈ ബ്രൗസറിൽ ശബ്ദ തിരിച്ചറിയൽ ലഭ്യമല്ല. ദയവായി ടൈപ്പ് ചെയ്യുക.",
    where_did_you_see: "എവിടെയാണ് കണ്ടത്?",
    where_helper: "സ്ഥലപ്പേര് അല്ലെങ്കിൽ അടുത്തുള്ള പ്രധാന അടയാളം (പരമാവധി 200 അക്ഷരങ്ങൾ)",
    where_placeholder: "ഉദാ: റെയിൽവേ സ്റ്റേഷന് സമീപം, ബസ് സ്റ്റാൻഡിന് പിന്നിൽ, മാർക്കറ്റ് ജംഗ്ഷൻ",
    district: "ജില്ല",
    select_district: "-- ജില്ല തിരഞ്ഞെടുക്കുക --",
    approx_time: "ഏകദേശ സമയം",
    approx_time_placeholder: "ഉദാഹരണത്തിന്: വൈകുന്നേരം 5:30 ഓടെ",
    photo_title: "വ്യക്തിയുടെ ഫോട്ടോ (നിർബന്ധമില്ല)",
    photo_helper: "നിങ്ങളുടെ കൈവശം ഫോട്ടോ ഉണ്ടെങ്കിലോ അകലെ നിന്ന് സുരക്ഷിതമായി എടുക്കാൻ സാധിക്കുമെങ്കിലോ മാത്രം നൽകുക. ഫോട്ടോ എടുക്കാൻ ആരോടും അടുക്കുകയോ പിന്തുടരുകയോ ചെയ്യരുത്.",
    photo_warning: "കുട്ടികളുടെ ഫോട്ടോ എടുക്കരുത്.",
    photo_take: "ഫോട്ടോ എടുക്കുക",
    photo_choose: "ഗാലറിയിൽ നിന്ന് തിരഞ്ഞെടുക്കുക",
    photo_remove: "ഫോട്ടോ നീക്കം ചെയ്യുക",
    photo_confirm_no_child: "ഈ ഫോട്ടോയിൽ കുട്ടി ഇല്ലെന്ന് ഞാൻ ഉറപ്പ് നൽകുന്നു.",
    photo_not_uploaded_notice: "ഈ ഡെമോയിൽ ഫോട്ടോകൾ അപ്‌ലോഡ് ചെയ്യില്ല.",
    immediate_danger_title: "കുട്ടി അടിയന്തിര അപകടത്തിലാണോ?",
    immediate_danger_yes: "അതെ",
    immediate_danger_no: "അല്ല",
    immediate_danger_not_sure: "ഉറപ്പില്ല",
    share_location: "എന്റെ ഏകദേശ സ്ഥലം (ഏകദേശം 1 കി.മീ) ജില്ലാ ശിശു സംരക്ഷണ ഓഫീസറുമായി പങ്കിടുക.",
    location_locating: "ലൊക്കേഷൻ കണ്ടെത്തുന്നു...",
    location_active: "ഏകദേശ ലൊക്കേഷൻ ഉൾപ്പെടുത്തി (~1 കി.മീ കൃത്യത).",
    location_denied: "ലൊക്കേഷൻ അനുമതി ലഭിച്ചില്ല. കോർഡിനേറ്റുകൾ ഇല്ലാതെ റിപ്പോർട്ട് അയക്കും.",
    location_out_of_bounds: "ലൊക്കേഷൻ കേരളത്തിന് പുറത്തായതിനാൽ പങ്കിടില്ല.",
    submit_report: "വിവരം സമർപ്പിക്കുക",
    submitting: "സമർപ്പിക്കുന്നു...",

    // Confirmation Screen
    report_success_title: "വിവരം വിജയകരമായി സമർപ്പിച്ചു",
    report_success_subtitle: "ജില്ലാ ഉദ്യോഗസ്ഥന്റെ പരിശോധനയ്ക്കായി നിങ്ങളുടെ ആശങ്ക സുരക്ഷിതമായി രേഖപ്പെടുത്തി.",
    case_ref_label: "റിപ്പോർട്ട് ഐഡി",
    reporter_token_label: "ഒറ്റത്തവണ കോൾബാക്ക് ടോക്കൺ",
    reporter_token_warning: "ഇത് ഇപ്പോൾ സേവ് ചെയ്യുക. ഇത് വീണ്ടും കാണിക്കാൻ സാധിക്കില്ല.",
    copy_token: "ടോക്കൺ കോപ്പി ചെയ്യുക",
    token_copied: "കോപ്പി ചെയ്തു!",
    callback_title: "തിരിച്ചുവിളിക്കാൻ അഭ്യർത്ഥിക്കുക",
    callback_desc: "നിങ്ങളുടെ വിവരങ്ങൾ വെളിപ്പെടുത്താതെ ഉദ്യോഗസ്ഥൻ ബന്ധപ്പെടാൻ ആഗ്രഹിക്കുന്നുവെങ്കിൽ:",
    callback_btn: "തിരിച്ചുവിളിക്കാൻ അഭ്യർത്ഥിക്കുക",
    callback_requested: "കോൾബാക്ക് അഭ്യർത്ഥിച്ചു. ഉദ്യോഗസ്ഥന് ഈ പോർട്ടൽ വഴി സുരക്ഷിതമായി വിളിക്കാം.",
    callback_already_requested: "ഈ റിപ്പോർട്ടിനായി കോൾബാക്ക് ഇതിനകം അഭ്യർത്ഥിച്ചിട്ടുണ്ട്.",
    submit_another: "മറ്റൊരു വിവരം നൽകുക",

    // Emergency Screen
    emergency_title: "അടിയന്തിര സഹായം",
    emergency_subtitle: "ഏറ്റവും അടുത്തുള്ള വനിതാ ഹെൽപ്പ്‌ലൈനിലേക്ക് വിളിക്കാൻ ഒരിക്കൽ ടാപ്പ് ചെയ്യുക. ഡയൽ ചെയ്യേണ്ടതില്ല.",
    start_call: "കോൾ ആരംഭിക്കുക",
    connecting: "കണക്റ്റ് ചെയ്യുന്നു...",
    emergency_privacy_note: "ഏറ്റവും അടുത്തുള്ള ഹെൽപ്പ്‌ലൈൻ കണ്ടെത്താൻ മാത്രമാണ് നിങ്ങളുടെ ലൊക്കേഷൻ ഉപയോഗിക്കുന്നത്. നിങ്ങളുടെ പേരോ ഫോൺ നമ്പറോ ചോദിക്കില്ല.",
    use_phone_dialer: "പകരം ഫോൺ ഡയലർ ഉപയോഗിക്കുക",
    opens_phone_dialer: "നിങ്ങളുടെ ഫോൺ ഡയലർ തുറക്കുന്നു",
    women_helpline: "വനിതാ ഹെൽപ്പ്‌ലൈൻ",
    connecting_message: "ഏറ്റവും അടുത്തുള്ള ഹെൽപ്പ്‌ലൈനിലേക്ക് ബന്ധിപ്പിക്കുന്നു...",
    connected_demo: "കണക്റ്റ് ആയി (ഡെമോ)",
    connected_tip: "നിങ്ങൾ എവിടെയാണെന്നും എന്താണ് സംഭവിക്കുന്നതെന്നും പറയുക.",
    end_call: "കോൾ അവസാനിപ്പിക്കുക",
    call_ended: "കോൾ അവസാനിച്ചു",
    call_duration: "ദൈർഘ്യം",
    write_report_now: "ഇപ്പോൾ റിപ്പോർട്ട് എഴുതുക",
    back_to_home: "തിരികെ ഹോമിലേക്ക്",
    emergency_district_label: "അടുത്തുള്ള ജില്ലാ ഹെൽപ്പ്‌ലൈൻ",

    // Officer Login Screen
    officer_signin_title: "ഓഫീസർ സൈൻ ഇൻ",
    officer_signin_subtitle: "റിപ്പോർട്ടുകൾ പരിശോധിക്കുന്ന പോലീസിനും ശിശുസംരക്ഷണ ഉദ്യോഗസ്ഥർക്കും ഉള്ളത്. റിപ്പോർട്ടർമാർക്ക് അക്കൗണ്ട് ആവശ്യമില്ല.",
    officer_id_or_email: "ഓഫീസർ ഐഡി അല്ലെങ്കിൽ ഔദ്യോഗിക ഇമെയിൽ",
    officer_id_placeholder: "ഉദാ: DCPU-TVM-01 അല്ലെങ്കിൽ officer@kerala.gov.in",
    password: "പാസ്‌വേഡ്",
    show_password: "കാണിക്കുക",
    hide_password: "മറയ്ക്കുക",
    forgot_password: "പാസ്‌വേഡ് മറന്നോ?",
    forgot_password_message: "ഓഫീസർ അക്കൗണ്ടുകൾ നിങ്ങളുടെ വകുപ്പാണ് നൽകുന്നത്. നിങ്ങളുടെ അഡ്മിനിസ്ട്രേറ്ററെ ബന്ധപ്പെടുക.",
    sign_in: "സൈൻ ഇൻ",
    signing_in: "സൈൻ ഇൻ ചെയ്യുന്നു...",
    officer_notice_line: "ഓഫീസർ അക്കൗണ്ടുകൾ നിങ്ങളുടെ വകുപ്പാണ് നൽകുന്നത്. പ്രവേശനത്തിനായി അഡ്മിനിസ്ട്രേറ്ററെ ബന്ധപ്പെടുക.",
    no_signin_needed_divider: "ഒരു ആശങ്ക അറിയിക്കണോ? ലോഗിൻ ആവശ്യമില്ല",

    // Categories
    cat_physical: "ശാരീരിക പീഡനം (Physical abuse)",
    cat_sexual: "ലൈംഗിക പീഡനം (Sexual abuse)",
    cat_emotional: "മാനസിക പീഡനം (Emotional abuse)",
    cat_neglect: "അവഗണന (Neglect)",
    cat_labour: "ബാലവേല (Child labour)",
    cat_marriage: "ബാലവിവാഹം (Child marriage)",
    cat_trafficking: "കടത്ത് (Trafficking)",
    cat_missing: "കാണാതായ കുട്ടി (Missing child)",
    cat_other: "മറ്റുള്ളവ (Other)",
  },
};

export const I18nContext = createContext({
  lang: "en",
  setLang: () => {},
  t: (key, fallback) => key,
});

export function I18nProvider({ children }) {
  const [lang, setLangState] = useState(() => {
    try {
      return localStorage.getItem("lang") || "en";
    } catch {
      return "en";
    }
  });

  const setLang = (newLang) => {
    setLangState(newLang);
    try {
      localStorage.setItem("lang", newLang);
    } catch (e) {
      console.warn("Could not save language to localStorage", e);
    }
  };

  const t = (key, fallback) => {
    return dictionary[lang]?.[key] ?? fallback ?? dictionary["en"]?.[key] ?? key;
  };

  return React.createElement(
    I18nContext.Provider,
    { value: { lang, setLang, t } },
    children
  );
}

export function useT() {
  return useContext(I18nContext);
}
