(function () {
  function ready(fn) {
    if (document.readyState !== 'loading') {
      fn();
    } else {
      document.addEventListener('DOMContentLoaded', fn);
    }
  }

  function stripHtml(value) {
    if (!value) return '';
    return value
      .replace(/<[^>]*>/g, ' ')
      .replace(/&nbsp;/gi, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function sectionHasContent(section) {
    const textareas = Array.from(section.querySelectorAll('textarea'));
    for (const textarea of textareas) {
      if (stripHtml(textarea.value).length > 0) {
        return true;
      }
    }

    const inputs = Array.from(section.querySelectorAll('input'))
      .filter(input => !['hidden', 'submit', 'button'].includes(input.type));

    for (const input of inputs) {
      if ((input.type === 'checkbox' || input.type === 'radio')) {
        if (input.checked) {
          return true;
        }
        continue;
      }

      if (stripHtml(input.value).length > 0) {
        return true;
      }
    }

    const selects = section.querySelectorAll('select');
    for (const select of selects) {
      if (stripHtml(select.value).length > 0) {
        return true;
      }
    }

    return false;
  }

  function sectionHasErrors(section) {
    if (section.querySelector('.error-block, .alert-danger')) {
      return true;
    }

    const invalidFields = section.querySelectorAll('input:invalid, textarea:invalid, select:invalid');
    return invalidFields.length > 0;
  }

  ready(function initialiseWaterForms() {
    const progressBlocks = document.querySelectorAll('.water-form-progress[data-water-progress]');
    if (!progressBlocks.length) {
      return;
    }

    progressBlocks.forEach(function (progressBlock) {
      const form = progressBlock.closest('form');
      if (!form) {
        return;
      }

      const sections = Array.from(form.querySelectorAll('fieldset.form-section'));
      if (!sections.length) {
        return;
      }

      const listContainer = progressBlock.querySelector('[data-progress-section-list]');
      if (!listContainer) {
        return;
      }
      listContainer.innerHTML = '';

      const labels = {
        pending: progressBlock.dataset.labelPending || 'Pending',
        complete: progressBlock.dataset.labelComplete || 'Complete',
        error: progressBlock.dataset.labelError || 'Needs review'
      };

      const sectionData = sections.map(function (section, index) {
        section.classList.add('water-form-section');
        if (!section.id) {
          const baseId = form.id || 'water-form';
          section.id = baseId + '-section-' + (index + 1);
        }

        const legend = section.querySelector('legend');
        const titleText = legend ? legend.textContent.trim() : 'Section ' + (index + 1);

        const card = document.createElement('button');
        card.type = 'button';
        card.className = 'progress-section-card';
        card.setAttribute('aria-controls', section.id);
        card.innerHTML = [
          '<span class="card-index">' + (index + 1) + '</span>',
          '<div class="card-body">',
          '  <span class="card-title">' + titleText + '</span>',
          '  <span class="card-status" data-status-text></span>',
          '</div>'
        ].join('');

        card.addEventListener('click', function () {
          section.scrollIntoView({ behavior: 'smooth', block: 'start' });
          section.classList.add('water-form-section--pulse');
          card.classList.add('is-active');
          setTimeout(function () {
            section.classList.remove('water-form-section--pulse');
            card.classList.remove('is-active');
          }, 750);
        });

        listContainer.appendChild(card);

        return {
          section: section,
          card: card,
          statusEl: card.querySelector('[data-status-text]')
        };
      });

      const completedStat = progressBlock.querySelector('[data-stat="completed"] .stat-value');
      const totalStat = progressBlock.querySelector('[data-stat="total"] .stat-value');
      const errorStat = progressBlock.querySelector('[data-stat="errors"] .stat-value');

      function updateProgress() {
        let completed = 0;
        let errors = 0;

        sectionData.forEach(function (item) {
          const hasContent = sectionHasContent(item.section);
          const hasError = sectionHasErrors(item.section);

          item.section.classList.toggle('is-complete', hasContent && !hasError);
          item.section.classList.toggle('has-errors', hasError);

          item.card.classList.toggle('is-complete', hasContent && !hasError);
          item.card.classList.toggle('has-errors', hasError);

          if (item.statusEl) {
            if (hasError) {
              item.statusEl.textContent = labels.error;
            } else if (hasContent) {
              item.statusEl.textContent = labels.complete;
            } else {
              item.statusEl.textContent = labels.pending;
            }
          }

          if (hasContent) {
            completed += 1;
          }
          if (hasError) {
            errors += 1;
          }
        });

        if (totalStat) {
          totalStat.textContent = sectionData.length;
        }
        if (completedStat) {
          completedStat.textContent = completed;
        }
        if (errorStat) {
          errorStat.textContent = errors;
        }
      }

      let updateScheduled = false;
      function scheduleUpdate() {
        if (updateScheduled) {
          return;
        }
        updateScheduled = true;
        window.requestAnimationFrame(function () {
          updateScheduled = false;
          updateProgress();
        });
      }

      updateProgress();

      form.addEventListener('input', scheduleUpdate, true);
      form.addEventListener('change', scheduleUpdate, true);
      form.addEventListener('blur', scheduleUpdate, true);

      const observer = new MutationObserver(scheduleUpdate);
      sectionData.forEach(function (item) {
        observer.observe(item.section, { childList: true, subtree: true, attributes: true });
      });
    });
  });
})();
