# coding=utf-8
"""Default InaSAFE Fields Step."""

# noinspection PyPackageRequirements
import logging
from PyQt4.QtGui import QWidget, QLabel

from safe.common.parameters.default_select_parameter import (
    DefaultSelectParameter)
from safe.common.parameters.default_select_parameter_widget import (
    DefaultSelectParameterWidget)
from safe_extras.parameters.qt_widgets.parameter_container import (
    ParameterContainer)

from safe.definitions.layer_purposes import (layer_purpose_aggregation)
from safe.definitions.utilities import get_fields, get_compulsory_fields
from safe.definitions.layer_geometry import layer_geometry_raster
from safe.definitions.constants import no_field
from safe.gui.tools.wizard.wizard_utils import get_inasafe_default_value_fields

from safe.definitions.fields import (
    youth_ratio_field, adult_ratio_field, elderly_ratio_field)

from safe.gui.tools.wizard.wizard_step import (
    WizardStep, get_wizard_step_ui_class)
from safe.utilities.i18n import tr

__copyright__ = "Copyright 2016, The InaSAFE Project"
__license__ = "GPL version 3"
__email__ = "info@inasafe.org"
__revision__ = '$Format:%H$'

FORM_CLASS = get_wizard_step_ui_class(__file__)
LOGGER = logging.getLogger('InaSAFE')


class StepKwDefaultInaSAFEFields(WizardStep, FORM_CLASS):
    """Keyword Wizard Step: Default InaSAFE Fields"""

    def __init__(self, parent=None):
        """Constructor for the tab.

        :param parent: parent - widget to use as parent (Wizard Dialog).
        :type parent: QWidget

        """
        WizardStep.__init__(self, parent)

        self.extra_parameters = [
            (DefaultSelectParameter, DefaultSelectParameterWidget)
        ]
        self.parameters = []
        self.parameter_container = ParameterContainer(
            extra_parameters=self.extra_parameters)
        self.kwExtraKeywordsGridLayout.addWidget(self.parameter_container)
        self.message_label = QLabel()

    def is_ready_to_next_step(self):
        """Check if the step is complete. If so, there is
            no reason to block the Next button.

        :returns: True if new step may be enabled.
        :rtype: bool
        """
        return True

    def get_next_step(self):
        """Find the proper step when user clicks the Next button.

        :returns: The step to be switched to
        :rtype: WizardStep instance or None
        """
        new_step = self.parent.step_kw_source
        return new_step

    def inasafe_fields_for_the_layer(self):
        """Return a list of inasafe fields the current layer.

        :returns: A list where each value represents inasafe field.
        :rtype: list
        """
        if (self.parent.get_layer_geometry_key() ==
                layer_geometry_raster['key']):
            return []
        # Get hazard or exposure value
        layer_purpose_key = self.parent.step_kw_purpose.selected_purpose()[
            'key']
        if layer_purpose_key != layer_purpose_aggregation['key']:
            subcategory_key = self.parent.step_kw_subcategory.\
                selected_subcategory()['key']
        else:
            subcategory_key = None
        # Get all fields with replace_null = True
        inasafe_fields = get_fields(
            layer_purpose_key, subcategory_key, replace_null=True)
        # remove compulsory field since it has been set in previous step
        try:
            inasafe_fields.remove(get_compulsory_fields(
                layer_purpose_key, subcategory_key))
        except ValueError:
            pass
        return inasafe_fields

    # noinspection PyTypeChecker
    def set_widgets(self):
        """Set widgets on the Extra Keywords tab."""
        self.clear()
        existing_inasafe_field = self.parent.get_existing_keyword(
            'inasafe_fields')
        existing_inasafe_default_values = self.parent.get_existing_keyword(
            'inasafe_default_values')
        # Remove old container and parameter
        if self.parameter_container:
            self.kwExtraKeywordsGridLayout.removeWidget(
                self.parameter_container)
        if self.parameters:
            self.parameters = []

        layer_data_provider = self.parent.layer.dataProvider()

        # Iterate through all inasafe fields
        # existing_inasafe_default_values

        for inasafe_field in self.inasafe_fields_for_the_layer():
            # Option for Not Available
            option_list = [no_field]
            for field in layer_data_provider.fields():
                # Check the field type
                if isinstance(inasafe_field['type'], list):
                    if field.type() in inasafe_field['type']:
                        field_name = field.name()
                        option_list.append('%s' % field_name)
                else:
                    if field.type() == inasafe_field['type']:
                        field_name = field.name()
                        option_list.append('%s' % field_name)

            # Create DefaultSelectParameter
            parameter = DefaultSelectParameter()
            parameter.guid = inasafe_field['key']
            parameter.name = inasafe_field['name']
            parameter.is_required = False
            parameter.description = inasafe_field['description']
            parameter.help_text = inasafe_field['help_text']
            parameter.element_type = unicode
            parameter.options_list = option_list
            parameter.value = no_field
            parameter.default_labels = get_inasafe_default_value_fields(
                self.parent.setting, inasafe_field['key'])[0]
            parameter.default_values = get_inasafe_default_value_fields(
                self.parent.setting, inasafe_field['key'])[1]
            parameter.minimum = inasafe_field['default_value'].get(
                'min_value')
            parameter.maximum = inasafe_field['default_value'].get(
                'max_value')
            # Check if there is already value in the metadata.
            if existing_inasafe_field:
                existing_value = existing_inasafe_field.get(
                    inasafe_field['key'])
                if existing_value:
                    if existing_value in parameter.options_list:
                        parameter.value = existing_value

            if existing_inasafe_default_values:
                existing_default_value = existing_inasafe_default_values.get(
                    inasafe_field['key'])
                if existing_default_value:
                    parameter.default = existing_default_value

            self.parameters.append(parameter)

        # Create the parameter container and add to the wizard.
        self.parameter_container = ParameterContainer(
            self.parameters, extra_parameters=self.extra_parameters)
        self.parameter_container.setup_ui()
        self.kwExtraKeywordsGridLayout.addWidget(self.parameter_container)
        # Add Message label
        self.kwExtraKeywordsGridLayout.addWidget(self.message_label)

        # Set default value to None
        for parameter_widget in self.parameter_container.\
                get_parameter_widgets():
            parameter_widget.widget().set_default(None)
            # Set selected radio button to 'Do not use'
            parameter_widget.widget().set_selected_radio_button()
        # Set default value from existing keywords
        if existing_inasafe_default_values:
            for guid, default in existing_inasafe_default_values.items():
                parameter_widget = self.parameter_container.\
                    get_parameter_widget_by_guid(guid)
                if isinstance(parameter_widget, DefaultSelectParameterWidget):
                    parameter_widget.set_default(default)
                    # Set selected radio button to 'Do not use'
                    parameter_widget.set_selected_radio_button()

    def get_inasafe_fields(self):
        """Return inasafe fields from the current wizard state.

        :returns: Dictionary of key and value from InaSAFE Fields.
        :rtype: dict
        """
        inasafe_fields = {}
        parameters = self.parameter_container.get_parameters(True)
        for parameter in parameters:
            if not parameter.value == no_field:
                inasafe_fields[parameter.guid] = parameter.value

        return inasafe_fields

    def get_inasafe_default_values(self):
        """Return inasafe default from the current wizard state.

        :returns: Dictionary of key and value from InaSAFE Default Values.
        :rtype: dict
        """
        inasafe_default_values = {}
        parameters = self.parameter_container.get_parameters(True)
        for parameter in parameters:
            if parameter.default is not None:
                inasafe_default_values[parameter.guid] = parameter.default

        return inasafe_default_values

    def clear(self):
        """Clear current state."""
        # Adapted from http://stackoverflow.com/a/13103617/1198772
        for i in reversed(range(self.kwExtraKeywordsGridLayout.count())):
            self.kwExtraKeywordsGridLayout.itemAt(i).widget().setParent(None)
        self.parameters = []
        self.parameter_container = ParameterContainer()

    def is_good_age_ratios(self):
        """Method to check the sum of age ratio is 1.

        :returns: True if the sum is 1 or the sum less than 1 but there is
            None.
        :rtype: bool
        """
        default_values = self.get_inasafe_default_values()

        youth_ratio = default_values.get(youth_ratio_field['key'])
        adult_ratio = default_values.get(adult_ratio_field['key'])
        elderly_ratio = default_values.get(elderly_ratio_field['key'])
        ratios = [youth_ratio, adult_ratio, elderly_ratio]

        if None in ratios:
            # If there is None, just check to not exceeding 1
            clean_ratios = [x for x in ratios if x is not None]
            ratios.remove(None)
            if sum(clean_ratios) > 1:
                return False
        else:
            if sum(ratios) != 1:
                return False

        return True

    def toggle_age_ratio_sum_message(self, flag):
        """Method to show error message about sum of age ratio.

        :param flag: Flag if the ratio is valid or not.
        :type flag: bool
        """
        if not flag:
            self.message_label.setText(
                tr('The sum of your age ratios is not 1. Please fix it '
                   'first before you can continue to the next step.'))
            self.message_label.setStyleSheet('color: red')
        else:
            self.message_label.setText(tr('You are good to go.'))
            self.message_label.setStyleSheet('color: green')
