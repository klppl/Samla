document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search-input');
    const resultsContainer = document.getElementById('search-results');
    const resultTemplate = document.getElementById('search-result-template'); // Optional, or string build

    let searchIndex = [];

    // Fetch Index
    fetch('/search.json')
        .then(response => response.json())
        .then(data => {
            searchIndex = data;
        })
        .catch(err => console.error('Failed to load search index:', err));

    // Search Logic
    const performSearch = (query) => {
        if (!query) {
            resultsContainer.innerHTML = '';
            return;
        }

        const lowerQuery = query.toLowerCase();

        // Simple scoring: Title match > Tag match > Content match
        const results = searchIndex.map(item => {
            let score = 0;
            if (item.title.toLowerCase().includes(lowerQuery)) score += 10;
            if (item.tags.some(tag => tag.toLowerCase().includes(lowerQuery))) score += 5;
            if (item.content.toLowerCase().includes(lowerQuery)) score += 1;

            return { item, score };
        })
            .filter(r => r.score > 0)
            .sort((a, b) => b.score - a.score)
            .slice(0, 20); // Top 20 results

        renderResults(results);
    };

    const renderResults = (results) => {
        resultsContainer.innerHTML = '';

        if (results.length === 0) {
            resultsContainer.innerHTML = '<p>No results found.</p>';
            return;
        }

        results.forEach(result => {
            const item = result.item;
            const div = document.createElement('div');
            div.className = 'post-item';
            div.style.marginBottom = '2rem';

            // Simple result layout
            div.innerHTML = `
                <div class="post-header">
                    <h2><a href="${item.url}">${item.title}</a></h2>
                    <div class="meta" style="color: var(--secondary-color); font-size: 0.85rem;">
                        <time>${item.date}</time> 
                        <span style="margin-left: 10px; text-transform: uppercase;">${item.type}</span>
                    </div>
                </div>
                <div class="post-excerpt">
                    ${getExcerpt(item.content, searchInput.value)}
                </div>
            `;
            resultsContainer.appendChild(div);
        });
    };

    const getExcerpt = (content, query) => {
        // Find query in content and show context
        const lowerContent = content.toLowerCase();
        const index = lowerContent.indexOf(query.toLowerCase());

        if (index === -1) return content.substring(0, 150) + '...';

        const start = Math.max(0, index - 50);
        const end = Math.min(content.length, index + 100);

        return '...' + content.substring(start, end) + '...';
    };

    // Debounce input
    let timeout = null;
    searchInput.addEventListener('input', (e) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            performSearch(e.target.value);
        }, 150);
    });
});
