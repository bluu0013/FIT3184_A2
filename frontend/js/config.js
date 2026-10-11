// Fill these in from the `sam deploy` outputs. None of these values are secrets.
export const config = {
  apiUrl: "REPLACE_ME",                 // ApiUrl output, e.g. https://abc123.execute-api.ap-southeast-2.amazonaws.com
  cognitoDomain: "REPLACE_ME",          // CognitoDomain output, e.g. ecoguard-team07.auth.ap-southeast-2.amazoncognito.com
  clientId: "REPLACE_ME",               // UserPoolClientId output
  redirectUri: window.location.origin + "/", // must match FrontendOrigin in the stack
};
