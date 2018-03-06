/**
 * Implementation of Google Tag Manager in React workspace using
 * https://github.com/holidaycheck/react-google-tag-manager
 *
 */

import React from "react";
import PropTypes from "prop-types";
import gtmParts from "react-google-tag-manager";

class GoogleTagManager extends React.Component {
    componentDidMount() {
        const dataLayerName = this.props.dataLayerName || "dataLayer";
        const scriptId = this.props.scriptId || "react-google-tag-manager-gtm";

        if (!window[dataLayerName]) {
            const gtmScriptNode = document.getElementById(scriptId);
            /*eslint-disable*/
            eval(gtmScriptNode.textContent);
            /*eslint-enable*/
        }
    }

    render() {
        const gtm = gtmParts({
            id: this.props.gtmId,
            dataLayerName: this.props.dataLayerName || "dataLayer",
            additionalEvents: this.props.additionalEvents || {},
            previewVariables: this.props.previewVariables || false
        });

        return (
            <div>
                <div>{gtm.noScriptAsReact()}</div>
                <div id={this.props.scriptId || "react-google-tag-manager-gtm"}>
                    {gtm.scriptAsReact()}
                </div>
            </div>
        );
    }
}

GoogleTagManager.propTypes = {
    gtmId: PropTypes.string.isRequired,
    dataLayerName: PropTypes.string,
    additionalEvents: PropTypes.object,
    previewVariables: PropTypes.string,
    scriptId: PropTypes.string
};

export default GoogleTagManager;
