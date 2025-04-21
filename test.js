document.addEventListener('DOMContentLoaded', () => {
  const loginButton = document.getElementById('login-button');
  const rocketElement = document.getElementById('single-rocket');
  const svgElement = document.querySelector('svg');
  const starsElement = document.getElementById('stars');
  const rocketsContainer = document.getElementById('rockets-container');

  let isDragging = false;
  let offsetX, offsetY;

  const startY = -225; // Начальная Y позиция за экраном
  const intermediateY = -125; // Промежуточная Y позиция
  const finalY = loginButton.getBoundingClientRect().bottom + rocketElement.offsetHeight + 50; // Конечная Y позиция ниже кнопки
  const startX = window.innerWidth / 2;
  const targetX = loginButton.getBoundingClientRect().left + loginButton.offsetWidth / 2 - rocketElement.offsetWidth / 2;
  const finalRotationAngle = -90;

  let animationProgress = 0;
  const animationDurationBeforeButton = 5000; // Длительность полета до промежуточной точки (мс)
  const animationDurationAfterButton = 5000; // Длительность полета после появления кнопки (мс)

  rocketElement.style.top = `${startY}%`;
  rocketElement.style.left = `${startX - rocketElement.offsetWidth / 2}px`;
  rocketElement.style.transform = `translateX(-50%) rotate(180deg)`; // Начальная ориентация вниз

  function animateRocket() {
    const currentTime = performance.now();
    let progress;
    let currentY;

    if (currentTime < 5000) {
      // Фаза 1: Полет до промежуточной точки (до появления кнопки)
      progress = Math.min(1, currentTime / animationDurationBeforeButton);
      currentY = startY + (intermediateY - startY) * progress;
    } else {
      // Фаза 2: Полет вниз после появления кнопки
      const elapsedTimeAfterButton = currentTime - 5000;
      progress = Math.min(1, elapsedTimeAfterButton / animationDurationAfterButton);
      currentY = intermediateY + (finalY - intermediateY) * progress;
    }

    rocketElement.style.top = `${currentY}%`;

    if (currentTime < 10000) {
      requestAnimationFrame(animateRocket);
    } else {
      // Финальная позиция и включение перетаскивания
      rocketElement.style.left = `${targetX - rocketElement.offsetWidth / 2}px`;
      rocketElement.style.transform = `translateX(-50%) rotate(${finalRotationAngle}deg)`;
      rocketElement.style.pointerEvents = 'auto';
    }
  }

  setTimeout(() => {
    loginButton.style.opacity = 1;
    loginButton.style.transform = 'translateY(0)';
    animateRocket(); // Запускаем анимацию ракеты после появления кнопки
  }, 5000); // Кнопка появляется через 5 секунд

  rocketElement.addEventListener('mousedown', (e) => startDrag(e));
  rocketElement.addEventListener('touchstart', (e) => startDrag(e));

  function startDrag(event) {
    isDragging = true;
    rocketElement.style.cursor = 'grabbing';
    rocketElement.style.animation = 'none'; // Отключаем JavaScript анимацию при перетаскивании
    let clientX, clientY;
    if (event.clientX !== undefined) {
      clientX = event.clientX;
      clientY = event.clientY;
    } else if (event.touches && event.touches.length > 0) {
      clientX = event.touches[0].clientX;
      clientY = event.touches[0].clientY;
    } else {
      return;
    }
    offsetX = clientX - rocketElement.getBoundingClientRect().left;
    offsetY = clientY - rocketElement.getBoundingClientRect().top;
  }

  document.addEventListener('mousemove', (e) => dragRocket(e));
  document.addEventListener('touchmove', (e) => dragRocket(e));

  function dragRocket(event) {
    if (!isDragging) return;
    let clientX, clientY;
    if (event.clientX !== undefined) {
      clientX = event.clientX;
      clientY = event.clientY;
    } else if (event.touches && event.touches.length > 0) {
      clientX = event.touches[0].clientX;
      clientY = event.touches[0].clientY;
    } else {
      return;
    }
    rocketElement.style.left = `${clientX - offsetX}px`;
    rocketElement.style.top = `${clientY - offsetY}px`;
  }

  document.addEventListener('mouseup', stopDrag);
  document.addEventListener('touchend', stopDrag);
  document.addEventListener('mouseleave', stopDrag);
  document.addEventListener('touchcancel', stopDrag);

  function stopDrag() {
    isDragging = false;
    rocketElement.style.cursor = 'grab';
  }

  function fadeOutElements() {
    rocketElement.style.transition = 'opacity 1s ease-in-out';
    rocketElement.style.opacity = 0;

    svgElement.style.transition = 'opacity 1s ease-in-out';
    svgElement.style.opacity = 0;

    loginButton.style.transition = 'opacity 1s ease-in-out';
    loginButton.style.opacity = 0;

    if (starsElement) {
      starsElement.style.transition = 'opacity 1s ease-in-out';
      starsElement.style.opacity = 0;
    }

    if (rocketsContainer) {
      rocketsContainer.style.transition = 'opacity 1s ease-in-out';
      rocketsContainer.style.opacity = 0;
    }

    setTimeout(() => {
      rocketElement.style.display = 'none';
      svgElement.style.display = 'none';
      loginButton.style.display = 'none';
      if (starsElement) {
        starsElement.style.display = 'none';
      }
      if (rocketsContainer) {
        rocketsContainer.style.display = 'none';
      }
    }, 1000);
  }

  loginButton.addEventListener('click', fadeOutElements);
});
