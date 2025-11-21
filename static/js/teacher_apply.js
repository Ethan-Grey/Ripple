function getCookie(name){const v=`; ${document.cookie}`.split(`; ${name}=`);if(v.length===2)return v.pop().split(';').shift();return ''}
const e = React.createElement;

function ApplyForm(){
  return e('form',{className:'rxA-form',method:'post',encType:'multipart/form-data'},[
    e('input',{type:'hidden',name:'csrfmiddlewaretoken',value:getCookie('csrftoken'),key:'csrf'}),
    
    // Info Card
    e('div', {className:'info-card', key:'info'}, [
      e('div', {className:'info-card-icon'}, '💡'),
      e('div', {className:'info-card-content'}, [
        e('h3', null, 'What happens next?'),
        e('p', null, 'Once you submit your application, our team will review it within 48 hours. We\'ll notify you via email whether you\'re approved to start teaching!')
      ])
    ]),
    
    // Basic Information Section
    e('div', {key:'basic'}, [
      e('h2', {className:'rxA-section-title'}, 'Basic Information'),
      e('div',{className:'rxA-field'},[
        e('label',null,'Class Title'), 
        e('input',{type:'text',name:'title',required:true,placeholder:'e.g., Intro to Digital Illustration'})
      ]),
      e('div',{className:'rxA-field'},[
        e('label', {className:'optional'}, 'Bio / About You'), 
        e('textarea',{name:'bio',rows:4,placeholder:'Tell learners about your background, experience, and teaching style...'})
      ])
    ]),
    
    // Class Details Section
    e('div', {key:'details'}, [
      e('h2', {className:'rxA-section-title'}, 'Class Details'),
      e('div',{className:'rxA-row'},[
        e('div',{className:'rxA-field'},[
          e('label',null,'Difficulty Level'), 
          e('select',{name:'difficulty',required:true},[
            e('option',{value:'beginner'},'Beginner'),
            e('option',{value:'intermediate'},'Intermediate'),
            e('option',{value:'advanced'},'Advanced')
          ])
        ]),
        e('div',{className:'rxA-field'},[
          e('label',null,'Can students trade?'), 
          e('select',{name:'is_tradeable',required:true},[
            e('option',{value:'false'},'No'),
            e('option',{value:'true'},'Yes')
          ])
        ])
      ]),
      e('div',{className:'rxA-row'},[
        e('div',{className:'rxA-field'},[
          e('label',null,'Duration (minutes)'), 
          e('input',{type:'number',name:'duration_minutes',min:0,placeholder:'e.g., 60',required:true}),
          e('span', {className:'rxA-helper'}, 'How long is your class?')
        ]),
        e('div',{className:'rxA-field'},[
          e('label',null,'Price ($)'), 
          e('input',{type:'number',step:'0.01',name:'price_dollars',min:0,placeholder:'e.g., 19.99',required:true}),
          e('span', {className:'rxA-helper'}, 'Set a fair price for your class')
        ])
      ])
    ]),
    
    // Media Section
    e('div', {key:'media'}, [
      e('h2', {className:'rxA-section-title'}, 'Media & Visuals'),
      e('div',{className:'rxA-row'},[
        e('div',{className:'rxA-field'},[
          e('label', {className:'optional'}, 'Intro Video (MP4)'), 
          e('input',{type:'file',name:'intro_video',accept:'video/*'}),
          e('span', {className:'rxA-helper'}, 'Show learners what to expect')
        ]),
        e('div',{className:'rxA-field'},[
          e('label', {className:'optional'}, 'Thumbnail Image'), 
          e('input',{type:'file',name:'thumbnail',accept:'image/*'}),
          e('span', {className:'rxA-helper'}, 'Make your class stand out')
        ])
      ])
    ]),
    
    // Additional Information Section
    e('div', {key:'additional'}, [
      e('h2', {className:'rxA-section-title'}, 'Additional Information'),
      e('div',{className:'rxA-row'},[
        e('div',{className:'rxA-field'},[
          e('label', {className:'optional'}, 'Portfolio Links'), 
          e('textarea',{name:'portfolio_links',rows:3,placeholder:'https://yourwebsite.com\nhttps://behance.net/yourprofile\n(One per line)'}),
          e('span', {className:'rxA-helper'}, 'Share your work with potential students')
        ]),
        e('div',{className:'rxA-field'},[
          e('label', {className:'optional'}, 'Expertise & Topics'), 
          e('textarea',{name:'expertise_topics',rows:3,placeholder:'Adobe Photoshop\nProcreate\nDigital Painting\n(One per line)'}),
          e('span', {className:'rxA-helper'}, 'What skills will you teach?')
        ])
      ])
    ]),
    
    // Actions
    e('div',{className:'rxA-actions', key:'actions'},[
      e('button',{className:'rxA-btn rxA-primary',type:'submit'},'Submit Application'),
      e('a',{href:'/classes/',className:'rxA-btn rxA-ghost'},'Cancel')
    ])
  ])
}

document.addEventListener('DOMContentLoaded', ()=>{
  const mount = document.getElementById('react-apply');
  if(mount){ ReactDOM.createRoot(mount).render(e(ApplyForm)); }
});