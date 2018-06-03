import React, { Component } from "react";
import { gql, graphql } from "react-apollo";
import { withRouter } from "react-router-dom";

import Header from "../Header";
import Footer from "../Footer";

class LogIn extends Component {
    constructor(props, context) {
        super(props, context);
        this.state = {
            form: { email: "", password: "" },
            login: false,
            errors: []
        };
    }

    handleChange(field, event) {
        let form = { ...this.state.form };
        form[field] = event.target.value;
        this.setState({ form: form });
    }

    /**
     * Handle login
     */
    handleSubmit = () => {
        this.setState({ errors: [], login: false });
        this.props
            .mutate({ variables: { ...this.state.form } })
            .then(({ data: { login } }) => {
                let state = { busy: false };
                if (login.login) {
                    login.login = true;
                    state.form = {
                        email: "",
                        password: ""
                    };
                    this.props.history.push("/");
                } else {
                    state.errors = login.errors;
                }
                this.setState(state);
            })
            .catch(error => {
                console.warn("there was an error sending the query", error);
                this.setState({ errors: [error.graphQLErrors[0].message] });
            });
    };

    /**
     * Alert to show on page
     * @returns JSX
     */
    getAlert() {
        const { errors } = this.state;
        if (errors.length)
            return (
                <div className="alert alert-danger">
                    <strong>Failed!</strong> The following error(s) have occured:
                    <ul>{errors.map((error, index) => <li key={index}>{error}</li>)}</ul>
                </div>
            );
    }

    render() {
        return (
            <div id="signup" className="login">
                <Header />
                <div className="body">
                    <h3 className="text-center">Sign In</h3>
                    {this.getAlert()}
                    <div className="form-group email">
                        <input
                            onChange={e => this.handleChange("email", e)}
                            type="email"
                            placeholder="Email address"
                            className="form-control"
                        />
                    </div>
                    <div className="form-group">
                        <input
                            onChange={e => this.handleChange("password", e)}
                            type="password"
                            placeholder="Password"
                            className="form-control"
                        />
                        <p>
                            <u>Forgot password</u>
                        </p>
                    </div>
                    <div className="form-group text-center">
                        <button onClick={this.handleSubmit}>SIGN IN</button>
                    </div>
                    <div className="form-group text-center border">
                        <h4>Do not have an account?</h4>
                        <a href="/signup">
                            <u>Sign up - 100% free</u>
                        </a>
                    </div>
                </div>
                <Footer />
            </div>
        );
    }
}

//  GraphQL mutation
const submitQuery = gql`
    mutation($email: String!, $password: String!) {
        login(email: $email, password: $password) {
            login
            errors
        }
    }
`;

const login = graphql(submitQuery)(LogIn);

export default withRouter(login);
