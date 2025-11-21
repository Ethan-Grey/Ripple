const input=document.getElementById('search-input');
if(input){
  input.addEventListener('input',()=>{
    const q=input.value.toLowerCase();
    document.querySelectorAll('.search-card').forEach(card=>{
      const k=(card.getAttribute('data-keywords')||'').toLowerCase();
      card.style.display=k.includes(q)?'':'none';
    });
  });
}