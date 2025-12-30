
document.addEventListener('DOMContentLoaded', () => {
    const toggles = document.querySelectorAll('.content-toggle');
    if (toggles.length === 0) return;

    // Only active on home page? User said "on the front page".
    // Or maybe everywhere? But typically stream is only on home.
    // Let's check if we are on home. 
    // Usually home path is '/' or '/index.html'
    const isHome = window.location.pathname === '/' || window.location.pathname === '/index.html' || document.body.classList.contains('home');

    // Wait, the detailed implementation plan said:
    // "User visits front page (/)... Clicking the toggle updates the state immediately... and saves to localStorage"

    // We should probably check if we are on a page that HAS the stream.
    // The stream items have `.post-item[data-type]`.
    const streamItems = document.querySelectorAll('.post-item[data-type]');
    const hasStream = streamItems.length > 0;

    // Load config defaults from a global object injected by the template?
    // Or verify if we can rely on data-attributes on the toggles which we didn't inject yet defaults.
    // Plan said: "Add data-default='{{ site.frontpage_filter[item.type] }}'"
    // I missed adding `data-default` in the previous step. Note to self: Add it or handle defaults in JS.
    // Actually, I can inject the defaults as a JSON object in the head or just infer from the initial `data-default` attribute on the button.

    // I need to update base.html again to add data-default if I want to rely on server-side config defaults.
    // Or I can just default to 'true' if not specified.

    toggles.forEach(toggle => {
        const type = toggle.dataset.type;

        // Load state
        const storedState = localStorage.getItem(`filter_${type}`);
        let limitState = true; // Default visible

        // Logic: Storage > Default?
        // Wait, I missed adding `data-default` to the button in step 751.
        // I will fix that in next step. Assuming it exists:
        // const defaultState = toggle.dataset.default === 'True'; 

        if (storedState !== null) {
            limitState = storedState === 'true';
        } else if (toggle.dataset.default) {
            // Respect config default (Python 'False' or 'True')
            const def = toggle.dataset.default.toLowerCase();
            limitState = def !== 'false' && def !== '0' && def !== 'none';
        } else {
            // Fallback if data-default missing
            limitState = true;
        }

        updateToggleUI(toggle, limitState);
        applyFilter(type, limitState);

        toggle.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation(); // Prevent nav link click if nested (it isn't anymore, but good practice)

            // Get current state from UI or storage
            const currentState = toggle.classList.contains('active');
            const newState = !currentState;

            localStorage.setItem(`filter_${type}`, newState);
            updateToggleUI(toggle, newState);
            applyFilter(type, newState);
        });
    });

    function updateToggleUI(element, isVisible) {
        if (isVisible) {
            element.classList.add('active');
            element.classList.remove('inactive');
        } else {
            element.classList.add('inactive');
            element.classList.remove('active');
        }
    }

    function applyFilter(type, isVisible) {
        // Find all items of this type
        const items = document.querySelectorAll(`.post-item[data-type="${type}"]`);
        items.forEach(item => {
            // Toggle the item itself
            if (isVisible) {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            }

            // Toggle the following divider if it exists
            const nextElement = item.nextElementSibling;
            if (nextElement && nextElement.classList.contains('post-divider')) {
                if (isVisible) {
                    nextElement.style.display = '';
                } else {
                    nextElement.style.display = 'none';
                }
            }
        });
    }
});
