[
    {% for c in classes %}
      {
        "slug": "{{ c.slug|escapejs }}",
        "title": "{{ c.title|escapejs }}",
        "thumb": "{% if c.thumbnail %}{{ c.thumbnail.url|escapejs }}{% endif %}",
        "teacher": "{{ c.teacher.username|escapejs }}",
        "difficulty": "{{ c.get_difficulty_display|escapejs }}",
        "duration": {{ c.duration_minutes|default:0 }},
        "rating": {{ c.avg_rating|default:0 }},
        "reviews": {{ c.reviews_count|default:0 }},
        "topics": [{% for t in c.topics.all|slice:":3" %}"{{ t.name|escapejs }}"{% if not forloop.last %}, {% endif %}{% endfor %}],
        "isEnrolled": {% if user.is_authenticated and c in user.enrolled_classes.all %}true{% else %}false{% endif %}
      }{% if not forloop.last %}, {% endif %}
    {% empty %}
    
    {% endfor %}
    ]

const e = React.createElement;

function Card({c}) {
  const href = `/classes/${c.slug}/`;
  return e('a', {href, className: 'class-card'}, [
    e('div', {className: 'thumb-wrap', key: 'img'}, [
      c.thumb 
        ? e('img', {className: 'thumb', src: c.thumb, alt: c.title})
        : e('div', {className: 'thumb-placeholder'}, c.title[0]?.toUpperCase() || 'C'),
      (c.rating > 0 && c.reviews > 0) 
        ? e('div', {className: 'rating-badge'}, `⭐ ${c.rating} · ${c.reviews}`)
        : null
    ]),
    e('div', {className: 'card-content', key: 'content'}, [
      e('div', {className: 'teacher-name'}, `By ${c.teacher}`),
      e('h3', {className: 'class-title'}, c.title),
      e('div', {className: 'topics-list'}, [
        ...(c.topics || []).slice(0, 3).map((t, i) => 
          e('span', {className: 'topic-pill', key: i}, t)
        ),
        (c.topics?.length > 3) 
          ? e('span', {className: 'topic-pill more', key: 'more'}, `+${c.topics.length - 3}`)
          : null
      ])
    ]),
    e('div', {className: 'card-footer', key: 'foot'}, [
      e('div', {className: 'card-meta'}, [
        e('span', {className: 'difficulty-badge', key: 'diff'}, c.difficulty),
        e('span', {className: 'meta-dot', key: 'dot'}, '•'),
        e('span', {className: 'duration', key: 'dur'}, [
          e('span', {key: 'icon'}, '⏱️'),
          `${c.duration}m`
        ])
      ]),
      e('div', {className: 'bookmark-icon', 'aria-hidden': 'true', key: 'bookmark'}, '🔖')
    ])
  ]);
}

function Grid() {
  const dataEl = document.getElementById('classes-data');
  const allItems = dataEl ? JSON.parse(dataEl.textContent || '[]') : [];
  
  // State for filtering and view mode
  const [showMyClasses, setShowMyClasses] = React.useState(false);
  const [viewMode, setViewMode] = React.useState('grid');
  
  // Filter items based on state
  const items = React.useMemo(() => {
    if (showMyClasses) {
      return allItems.filter(item => item.isEnrolled);
    }
    return allItems;
  }, [showMyClasses, allItems]);
  
  // Setup My Classes filter button click handler
  React.useEffect(() => {
    const myClassesBtn = document.getElementById('my-classes-filter');
    if (myClassesBtn) {
      const handleClick = () => {
        setShowMyClasses(prev => !prev);
        myClassesBtn.classList.toggle('active');
      };
      myClassesBtn.addEventListener('click', handleClick);
      return () => myClassesBtn.removeEventListener('click', handleClick);
    }
  }, []);
  
  // Setup Grid/List view toggle handlers
  React.useEffect(() => {
    const gridBtn = document.getElementById('grid-view-btn');
    const listBtn = document.getElementById('list-view-btn');
    
    const handleGridClick = () => {
      setViewMode('grid');
      gridBtn.classList.add('active');
      listBtn.classList.remove('active');
    };
    
    const handleListClick = () => {
      setViewMode('list');
      listBtn.classList.add('active');
      gridBtn.classList.remove('active');
    };
    
    if (gridBtn && listBtn) {
      gridBtn.addEventListener('click', handleGridClick);
      listBtn.addEventListener('click', handleListClick);
      
      return () => {
        gridBtn.removeEventListener('click', handleGridClick);
        listBtn.removeEventListener('click', handleListClick);
      };
    }
  }, []);
  
  if (items.length === 0) {
    const message = showMyClasses 
      ? "You haven't enrolled in any classes yet" 
      : 'Try adjusting your filters to find what you\'re looking for.';
    const title = showMyClasses ? 'No enrolled classes' : 'No classes found';
    
    return e('div', {className: 'empty-state'}, [
      e('div', {className: 'empty-icon', key: 'icon'}, '📚'),
      e('h3', {className: 'empty-title', key: 'title'}, title),
      e('p', {className: 'empty-text', key: 'text'}, message)
    ]);
  }
  
  // Use different className based on view mode
  const containerClass = viewMode === 'grid' ? 'classes-grid' : 'classes-list';
  
  return e('div', {className: containerClass}, 
    items.map((c, i) => e(Card, {c, key: i}))
  );
}

document.addEventListener('DOMContentLoaded', () => {
  const mount = document.getElementById('react-class-grid');
  if (mount) {
    const root = ReactDOM.createRoot(mount);
    root.render(e(Grid));
  }
});