const base = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
async function check(response){const body=await response.json().catch(()=>({}));if(!response.ok)throw new Error(body.detail || "Request failed ("+response.status+")");return body;}
export async function askQuestion(query,history=[]){return check(await fetch(base+"/qa",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({query,history})}));}
export async function searchCases(query){return check(await fetch(base+"/search",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({query})}));}
export async function analyzeDocument(file,query){const data=new FormData();data.append("file",file);data.append("query",query);return check(await fetch(base+"/document-analysis",{method:"POST",body:data}));}
export async function checkHealth(){return check(await fetch(base+"/health"));}
