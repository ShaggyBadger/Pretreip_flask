function clickListener(e) {
  console.log('Clicked!', e);
}

document.addEventListener('click', clickListener);

// tester.js

async function fetchAndProcessUsers(apiUrl) {
  try {
    console.log('Fetching user data from:', apiUrl);

    // fetch data from API
    const response = await fetch(apiUrl);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

    const users = await response.json();

    // filter active users, sort by last login descending, and map to summary objects
    const processed = users
      .filter((user) => user.isActive)
      .sort((a, b) => new Date(b.lastLogin) - new Date(a.lastLogin))
      .map((user) => ({
        id: user.id,
        name: `${user.firstName} ${user.lastName}`,
        lastLogin: user.lastLogin,
        email: user.email,
        roles: user.roles.join(', '),
      }));

    console.log('Processed users:', processed);
    return processed;
  } catch (err) {
    console.error('Error fetching or processing users:', err);
    return [];
  }
}

// Example usage
fetchAndProcessUsers('https://jsonplaceholder.typicode.com/users').then(
  (users) => {
    console.log('Fetched and processed', users.length, 'users');
  },
);
