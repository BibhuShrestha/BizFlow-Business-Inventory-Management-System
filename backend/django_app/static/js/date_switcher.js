/**
 * BizFlow Dual BS / AD Date Picker & Switcher
 * Provides bidirectional live conversion between Gregorian (AD) and Bikram Sambat (BS).
 * Keeps the underlying input synchronized with AD date (YYYY-MM-DD) for seamless backend persistence.
 */

(function () {
  'use strict';

  var NEPALI_MONTHS = [
    { id: 1, name: 'Baisakh', np: 'वैशाख' },
    { id: 2, name: 'Jestha', np: 'जेठ' },
    { id: 3, name: 'Ashadh', np: 'असार' },
    { id: 4, name: 'Shrawan', np: 'साउन' },
    { id: 5, name: 'Bhadra', np: 'भदौ' },
    { id: 6, name: 'Ashwin', np: 'असोज' },
    { id: 7, name: 'Kartik', np: 'कार्तिक' },
    { id: 8, name: 'Mangsir', np: 'मंसिर' },
    { id: 9, name: 'Poush', np: 'पुष' },
    { id: 10, name: 'Magh', np: 'माघ' },
    { id: 11, name: 'Falgun', np: 'फागुन' },
    { id: 12, name: 'Chaitra', np: 'चैत' }
  ];

  var conversionCache = {};

  function fetchConversion(dateStr, mode, callback) {
    var key = dateStr + '_' + mode;
    if (conversionCache[key]) {
      callback(conversionCache[key]);
      return;
    }

    var url = '/api/convert-date/?date=' + encodeURIComponent(dateStr) + '&mode=' + encodeURIComponent(mode);
    fetch(url)
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (data && data.success) {
          conversionCache[key] = data;
          callback(data);
        }
      })
      .catch(function (err) {
        console.warn('Date conversion failed:', err);
      });
  }

  function initDateSwitcher(inputEl) {
    if (inputEl.dataset.dateSwitcherInitialized) return;
    inputEl.dataset.dateSwitcherInitialized = 'true';

    var isCompact = inputEl.closest('form')?.classList.contains('filter-form') ||
                    inputEl.parentElement?.classList.contains('compact-date') ||
                    inputEl.offsetWidth < 180;

    // Create container
    var wrapper = document.createElement('div');
    wrapper.className = 'bizflow-date-switcher ' + (isCompact ? 'compact' : '');
    wrapper.style.display = 'flex';
    wrapper.style.flexDirection = 'column';
    wrapper.style.gap = '4px';
    wrapper.style.position = 'relative';

    inputEl.parentNode.insertBefore(wrapper, inputEl);
    wrapper.appendChild(inputEl);

    // Create header with AD/BS toggle and badge
    var header = document.createElement('div');
    header.className = 'bizflow-date-header';
    header.style.display = 'flex';
    header.style.alignItems = 'center';
    header.style.justifyContent = 'space-between';
    header.style.fontSize = '11px';
    header.style.marginBottom = '2px';

    // Segmented toggle button
    var toggleGroup = document.createElement('div');
    toggleGroup.className = 'date-mode-toggle';
    toggleGroup.style.display = 'inline-flex';
    toggleGroup.style.border = '1px solid #cbd5e1';
    toggleGroup.style.borderRadius = '4px';
    toggleGroup.style.overflow = 'hidden';
    toggleGroup.style.background = '#f1f5f9';

    var btnAD = document.createElement('button');
    btnAD.type = 'button';
    btnAD.textContent = 'AD';
    btnAD.className = 'btn-toggle-ad active';
    styleToggleButton(btnAD, true);

    var btnBS = document.createElement('button');
    btnBS.type = 'button';
    btnBS.textContent = 'BS';
    btnBS.className = 'btn-toggle-bs';
    styleToggleButton(btnBS, false);

    toggleGroup.appendChild(btnAD);
    toggleGroup.appendChild(btnBS);

    // Live converted badge
    var badge = document.createElement('span');
    badge.className = 'date-preview-badge';
    badge.style.fontSize = '11px';
    badge.style.fontWeight = '500';
    badge.style.color = '#3730a3';
    badge.style.background = '#e0e7ff';
    badge.style.padding = '1px 6px';
    badge.style.borderRadius = '4px';
    badge.style.whiteSpace = 'nowrap';
    badge.textContent = 'BS Date...';

    header.appendChild(toggleGroup);
    header.appendChild(badge);
    wrapper.insertBefore(header, inputEl);

    // Create BS inputs container
    var bsContainer = document.createElement('div');
    bsContainer.className = 'bizflow-bs-input-group';
    bsContainer.style.display = 'none';
    bsContainer.style.gap = '4px';
    bsContainer.style.alignItems = 'center';

    // BS Year select (2070 to 2090)
    var selYear = document.createElement('select');
    selYear.className = 'form-control bs-sel-year';
    selYear.style.padding = '4px 6px';
    selYear.style.fontSize = '12px';
    selYear.style.height = '34px';
    selYear.style.width = '80px';
    for (var y = 2070; y <= 2090; y++) {
      var optY = document.createElement('option');
      optY.value = y;
      optY.textContent = y;
      if (y === 2083) optY.selected = true;
      selYear.appendChild(optY);
    }

    // BS Month select
    var selMonth = document.createElement('select');
    selMonth.className = 'form-control bs-sel-month';
    selMonth.style.padding = '4px 6px';
    selMonth.style.fontSize = '12px';
    selMonth.style.height = '34px';
    selMonth.style.flex = '1';
    selMonth.style.minWidth = '95px';
    NEPALI_MONTHS.forEach(function (m) {
      var optM = document.createElement('option');
      optM.value = m.id;
      optM.textContent = m.name + ' (' + m.np + ')';
      selMonth.appendChild(optM);
    });

    // BS Day select (1 to 32)
    var selDay = document.createElement('select');
    selDay.className = 'form-control bs-sel-day';
    selDay.style.padding = '4px 6px';
    selDay.style.fontSize = '12px';
    selDay.style.height = '34px';
    selDay.style.width = '60px';
    for (var d = 1; d <= 32; d++) {
      var optD = document.createElement('option');
      optD.value = d;
      optD.textContent = d < 10 ? '0' + d : d;
      selDay.appendChild(optD);
    }

    bsContainer.appendChild(selYear);
    bsContainer.appendChild(selMonth);
    bsContainer.appendChild(selDay);
    wrapper.appendChild(bsContainer);

    function setMode(mode) {
      if (mode === 'BS') {
        inputEl.style.display = 'none';
        bsContainer.style.display = 'flex';
        styleToggleButton(btnBS, true);
        styleToggleButton(btnAD, false);
      } else {
        inputEl.style.display = 'block';
        bsContainer.style.display = 'none';
        styleToggleButton(btnAD, true);
        styleToggleButton(btnBS, false);
      }
    }

    btnAD.addEventListener('click', function () { setMode('AD'); });
    btnBS.addEventListener('click', function () { setMode('BS'); });

    // Sync from AD input to BS
    function syncFromAD() {
      var val = inputEl.value;
      if (!val) {
        badge.textContent = 'No date';
        return;
      }
      fetchConversion(val, 'ad_to_bs', function (data) {
        badge.textContent = data.bs_date + ' BS (' + data.bs_month_name + ')';
        if (data.bs_year) selYear.value = data.bs_year;
        if (data.bs_month) selMonth.value = data.bs_month;
        if (data.bs_day) selDay.value = data.bs_day;
      });
    }

    // Sync from BS dropdowns to AD input
    function syncFromBS() {
      var y = selYear.value;
      var m = selMonth.value;
      var d = selDay.value;
      var bsDateStr = y + '-' + (m < 10 ? '0' + m : m) + '-' + (d < 10 ? '0' + d : d);

      fetchConversion(bsDateStr, 'bs_to_ad', function (data) {
        if (data.ad_date) {
          inputEl.value = data.ad_date;
          badge.textContent = data.bs_date + ' BS (' + data.formatted_ad + ' AD)';
          // Trigger change event on input for other listeners
          var evt = new Event('change', { bubbles: true });
          inputEl.dispatchEvent(evt);
        }
      });
    }

    inputEl.addEventListener('change', syncFromAD);
    inputEl.addEventListener('input', syncFromAD);

    selYear.addEventListener('change', syncFromBS);
    selMonth.addEventListener('change', syncFromBS);
    selDay.addEventListener('change', syncFromBS);

    // Initial sync
    if (inputEl.value) {
      syncFromAD();
    } else {
      // Default to today if needed or fetch today's conversion
      fetchConversion('', 'ad_to_bs', function (data) {
        if (!inputEl.value && inputEl.required) {
          inputEl.value = data.ad_date;
        }
        badge.textContent = data.bs_date + ' BS (' + data.bs_month_name + ')';
        if (data.bs_year) selYear.value = data.bs_year;
        if (data.bs_month) selMonth.value = data.bs_month;
        if (data.bs_day) selDay.value = data.bs_day;
      });
    }
  }

  function styleToggleButton(btn, isActive) {
    btn.style.border = 'none';
    btn.style.padding = '2px 8px';
    btn.style.fontSize = '10.5px';
    btn.style.fontWeight = '600';
    btn.style.cursor = 'pointer';
    btn.style.transition = 'all 0.15s ease';
    if (isActive) {
      btn.style.background = '#1E40AF';
      btn.style.color = '#ffffff';
    } else {
      btn.style.background = 'transparent';
      btn.style.color = '#64748b';
    }
  }

  function scanAndInit() {
    var dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(function (inp) {
      initDateSwitcher(inp);
    });
  }

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', scanAndInit);
  } else {
    scanAndInit();
  }

  // Export helper globally so modals and dynamic forms can re-trigger initialization
  window.BizFlowDateSwitcher = {
    init: initDateSwitcher,
    scan: scanAndInit
  };
})();
