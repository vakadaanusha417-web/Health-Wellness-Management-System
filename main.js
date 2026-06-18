const now = new Date();
const remindersSection = document.querySelector('.reminder-list');
if (remindersSection) {
    const reminders = document.querySelectorAll('.reminder-list li');
    if (reminders.length > 0) {
        reminders.forEach(reminder => {
            const text = reminder.textContent;
            const timeMatch = text.match(/at\s*(\d{2}:\d{2})/);
            if (timeMatch) {
                const reminderTime = timeMatch[1];
                const [hours, minutes] = reminderTime.split(':').map(Number);
                const nowH = now.getHours();
                const nowM = now.getMinutes();
                if (hours === nowH && minutes === nowM) {
                    alert(`It's time to take your medicine: ${text}`);
                }
            }
        });
    }
}

const firstAidSelector = document.getElementById('firstAidSelector');
const firstAidAdvice = document.getElementById('firstAidAdvice');
if (firstAidSelector && firstAidAdvice) {
    firstAidSelector.addEventListener('change', () => {
        const selectedOption = firstAidSelector.options[firstAidSelector.selectedIndex];
        const advice = selectedOption.dataset.advice;
        if (advice) {
            firstAidAdvice.innerHTML = `<p>${advice}</p>`;
        } else {
            firstAidAdvice.innerHTML = '<p>Select a topic to see first aid advice here.</p>';
        }
    });
}
