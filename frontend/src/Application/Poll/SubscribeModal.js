/**
 * Created by vathavaria on 6/23/17.
 */

import React, { Component } from "react";
import { withCookies, Cookies } from "react-cookie";
import { ControlLabel, FormControl, FormGroup } from "react-bootstrap";
import { graphql, gql } from "react-apollo";
import PropTypes from "prop-types";
import ReactGA from "react-ga";

class SubscribeModal extends Component {
    initializeState() {
        return {
            showSelf: true,
            fullname: "",
            fullnameValidation: null,
            emailAddress: "",
            emailValidation: null,
            showShareReviewModal: false,
            reviewId: null,
            error: null
        };
    }

    constructor(props, context) {
        super(props, context);
        this.state = this.initializeState();
    }

    componentWillReceiveProps() {
        this.setState(this.initializeState());
    }

    componentWillMount() {
        const { cookies } = this.props;
        this.setState({ rated: cookies.get("rated") || {} });
    }

    render() {
        const {
            politicianId,
            reviewText,
            cookies,
            approved,
            location,
            mutate,
            tags,
            next
        } = this.props;
        const { rated } = this.state;
        const sentiment = approved ? "positive" : "negative";

        const validateEmail = email => {
            const re = /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@(([[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
            return re.test(email);
        };

        const onSubmit = () => {
            ReactGA.event({
                category: "User",
                action: "Modal_FinalGetUpdates",
                label: "Skip"
            });
            mutate({
                variables: {
                    politicianId: politicianId,
                    sentiment: sentiment,
                    body: reviewText,
                    fullName: this.state.fullname,
                    emailAddress: this.state.emailAddress,
                    tags: tags,
                    location: `${location.state || ""},${location.country},${location.postalCode ||
                        ""}`
                }
            })
                .then(({ data }) => {
                    rated[politicianId] = approved ? "approved" : "disapproved";
                    cookies.set("rated", rated, { path: "/" });
                    window.store = {};
                    next({ reviewId: data.createReview.review.id });
                })
                .catch(error => {
                    console.warn("there was an error sending the query", error);
                    this.setState({ error: error.graphQLErrors[0].message });
                });
        };

        const onSubmitWithUserValidation = () => {
            let errorState = {};
            let validationErrors = false;

            if (this.state.fullname === "") {
                errorState.fullnameValidation = "error";
                validationErrors = true;
            }

            if (this.state.emailAddress === "" || !validateEmail(this.state.emailAddress)) {
                errorState.emailValidation = "error";
                validationErrors = true;
            }

            if (validationErrors) {
                this.setState(errorState);
            } else {
                ReactGA.event({
                    category: "User",
                    action: "Modal_FinalGetUpdates",
                    label: "Submit"
                });
                onSubmit();
            }
        };

        const fullnameTextChange = e => {
            if (e.key !== "Enter") {
                this.setState({
                    fullname: e.target.value,
                    fullnameValidation: null
                });
            }
        };

        const emailAddressTextChange = e => {
            if (e.key !== "Enter") {
                this.setState({
                    emailAddress: e.target.value,
                    emailValidation: null
                });
            }
        };

        return (
            <div className="texto_modales_center">
                <div className="texto_modales mb10">Get Updates from DonaldTrumpReviews.com</div>
                <div className="modal_text_small opinion">
                    Your name and contact information will NOT be displayed publicly. Your review
                    will remain anonymous.
                </div>
                {this.state.error && (
                    <div className="text-center text-danger">{this.state.error}</div>
                )}
                <form className="user-d">
                    <FormGroup validationState={this.state.fullnameValidation}>
                        <ControlLabel>Full name</ControlLabel>
                        <FormControl
                            id="fullnametxt"
                            type="text"
                            placeholder="Enter your name"
                            onChange={fullnameTextChange}
                        />
                    </FormGroup>
                    <FormGroup validationState={this.state.emailValidation}>
                        <ControlLabel>E-mail</ControlLabel>
                        <FormControl
                            id="emailtxt"
                            type="email"
                            placeholder="Enter your e-mail"
                            onChange={emailAddressTextChange}
                        />
                    </FormGroup>
                </form>
                <div className="form-group text-center m0">
                    <button
                        type="button"
                        className="btn btn-modal btn-primary"
                        onClick={onSubmitWithUserValidation.bind(this)}
                    >
                        Submit
                    </button>
                </div>
            </div>
        );
    }
}

SubscribeModal.propTypes = {
    cookies: PropTypes.instanceOf(Cookies).isRequired
};

const submitQuery = gql`
    mutation createReview(
        $politicianId: ID!
        $sentiment: String!
        $body: String!
        $fullName: String!
        $emailAddress: String!
        $location: String!
        $tags: [Tag]!
    ) {
        createReview(
            politicianId: $politicianId
            sentiment: $sentiment
            body: $body
            location: $location
            tags: $tags
            fullName: $fullName
            emailAddress: $emailAddress
        ) {
            review {
                id
            }
        }
    }
`;

const SubscribeModalWithMutation = graphql(submitQuery)(SubscribeModal);

export default withCookies(SubscribeModalWithMutation);
